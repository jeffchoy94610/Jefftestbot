#from birdy.twitter import UserClient
from html_telegraph_poster import TelegraphPoster
import json
import re
import requests
import re
from lxml import html
from lxml.html.clean import Cleaner
import requests
from requests.compat import urlparse, quote_plus
from requests_toolbelt import MultipartEncoder

base_url = 'https://telegra.ph'
save_url = 'https://edit.telegra.ph/save'
default_user_agent = 'Python_telegraph_poster/0.1'
allowed_tags = ['a', 'aside', 'b', 'blockquote', 'br', 'em', 'figcaption', 'figure', 'h3', 'h4', 'hr', 'i', 'iframe',
                'img', 'li', 'ol', 'p', 's', 'strong', 'u', 'ul', 'video']
allowed_top_level_tags = ['aside', 'blockquote', 'figure', 'h3', 'h4', 'hr', 'ol', 'p', 'ul']

youtube_re = re.compile(r'(https?:)?//(www\.)?youtube(-nocookie)?\.com/embed/')
vimeo_re = re.compile(r'(https?:)?//player\.vimeo\.com/video/(\d+)')
twitter_re = re.compile(r'(https?:)?//(www\.)?twitter\.com/[A-Za-z0-9_]{1,15}/status/\d+')


def clean_article_html(html_string):

    html_string = html_string.replace('<h1', '<h3').replace('</h1>', '</h3>')
    # telegram will convert <b> anyway
    html_string = re.sub(r'<(/?)b(?=\s|>)', r'<\1strong', html_string)
    html_string = re.sub(r'<(/?)(h2|h5|h6)', r'<\1h4', html_string)

    c = Cleaner(
        allow_tags=allowed_tags,
        style=True,
        remove_unknown_tags=False,
        embedded=False
    )
    # wrap with div to be sure it is there
    # (otherwise lxml will add parent element in some cases
    html_string = '<div>%s</div>' % html_string
    cleaned = c.clean_html(html_string)
    # remove wrapped div
    cleaned = cleaned[5:-6]
    # remove all line breaks and empty strings (in html it means nothing)
    html_string = re.sub('(^[\s\t]*)?\r?\n', '', cleaned, flags=re.MULTILINE)
    # but replace multiple br tags with one line break, telegraph will convert it to <br class="inline">
    html_string = re.sub(r'(<br(/?>|\s[^<>]*>)\s*)+', '\n', html_string)

    return html_string.strip(' \t')


def _wrap_tag(element, wrapper):
    new_element = html.HtmlElement()
    new_element.tag = wrapper
    new_element.append(element)
    return new_element


def preprocess_media_tags(element):
    if isinstance(element, html.HtmlElement):
        if element.tag == 'figcaption':
            # figcaption may have only text content
            [e.drop_tag() for e in element.findall('*')]
        elif element.tag in ['ol', 'ul']:
            # ignore any spaces between <ul> and <li>
            element.text = ''
        elif element.tag == 'li':
            # ignore spaces after </li>
            element.tail = ''
        elif element.tag == 'iframe' and element.get('src'):
            iframe_src = element.get('src')
            youtube = youtube_re.match(iframe_src)
            vimeo = vimeo_re.match(iframe_src)
            if youtube or vimeo:
                if youtube:
                    yt_id = urlparse(iframe_src).path.replace('/embed/', '')
                    element.set('src', '/embed/youtube?url=' + quote_plus('https://www.youtube.com/watch?v=' + yt_id))
                elif vimeo:
                    element.set('src', '/embed/vimeo?url=' + quote_plus('https://vimeo.com/' + vimeo.group(2)))

                element = _wrap_tag(element, 'figure')
        elif element.tag == 'blockquote' and element.get('class') == 'twitter-tweet':
            twitter_links = element.cssselect('a')
            for tw_link in twitter_links:
                if twitter_re.match(tw_link.get('href')):
                    twitter_frame = html.HtmlElement()
                    twitter_frame.tag = 'iframe'
                    twitter_frame.set('src', '/embed/twitter?url=' + quote_plus(tw_link.get('href')))
                    element = _wrap_tag(twitter_frame, 'figure')

    return element


def preprocess_fragments(fragments):
    processed_fragments = []
    bad_tags = []

    if not len(fragments):
        return processed_fragments

    # convert and append text node before starting tag
    if not isinstance(fragments[0], html.HtmlElement):
        if len(fragments[0].strip()) > 0:
            processed_fragments.append(html.fromstring('<p>%s</p>' % fragments[0]))
        fragments.pop(0)
        if not len(fragments):
            return processed_fragments

    for fragment in fragments:
        # figure should be on the top level
        if fragment.find('figure') is not None:
            f = fragment.find('figure')
            processed_fragments.append(f)
            fragment.remove(f)

        processed_fragments.append(fragment)
    # bad iframes
    bad_tags.extend(fragments[-1].xpath('//iframe[not(@src) or @src=""]'))
    # bad lists (remove lists/list items if empty)
    nodes_not_to_be_empty = fragments[-1].xpath('//ul|//ol|//li|//p')
    bad_tags.extend([x for x in nodes_not_to_be_empty if len(x.text_content().strip()) == 0])

    for bad_tag in bad_tags:
        bad_tag.drop_tag()
        if bad_tag in fragments:
            fragments.remove(bad_tag)
        if bad_tag in processed_fragments:
            processed_fragments.remove(bad_tag)

    return processed_fragments


def _recursive_convert(element):

    element = preprocess_media_tags(element)
    fragment_root_element = {
        'tag': element.tag
    }

    content = []
    if element.text:
        content.append(element.text)

    if element.attrib:
        fragment_root_element.update({
            'attrs': dict(element.attrib)
        })

    for child in element:
        content.append(_recursive_convert(child))
        # Append Text node after element, if exists
        if child.tail:
            content.append(child.tail)

    if len(content):
        fragment_root_element.update({
            'children': content
        })

    return fragment_root_element


def convert_html_to_telegraph_format(html_string, clean_html=True):
    if clean_html:
        html_string = clean_article_html(html_string)

    fragments = preprocess_fragments(
        html.fragments_fromstring(html_string)
    )
    content = []

    for fragment in fragments:

        if fragment.tag not in allowed_top_level_tags:
            paragraph = html.HtmlElement()
            paragraph.tag = 'p'
            paragraph.append(fragment)
            content.append(_recursive_convert(paragraph))
        else:
            content.append(_recursive_convert(fragment))

            # convert and append text nodes after closing tag
            if fragment.tail and len(fragment.tail.strip()) != 0:
                content.append(
                    _recursive_convert(html.fromstring('<p>%s</p>' % fragment.tail))
                )

    return json.dumps(content, ensure_ascii=False)


TELEGRAPH = "20346be13b984c8e63d3d9e90aea7fa2e363f72110ef3cdc3a2281be8505"


def telegraph(message):
    name = message.from_user.first_name
    if message.from_user.last_name is not None:
        name += " " + message.from_user.last_name
    msg = "<h1>Submitted From: %s</h><br>" % name
    para = message.text.split("\n")
    for each in para:
        msg += "<p>%s</p>" % each
    #msg = message
    #content = ""
    content = convert_html_to_telegraph_format(msg)
    title = "Lil Corgi Bot Auto-Generated Post"
    
    posturl = 'https://api.telegra.ph/createPage?access_token=%s&title=%s&author_name=Lil Corgi Bot&author_url=http://telegram.me/jefftest2bot&content=%s&return_content=True' % (TELEGRAPH, title, content)
    print(posturl)
    r = requests.get(posturl)
    data = json.loads(r.text)
    print(data)
    output = data['result']['url']
    print(output)
    return output

