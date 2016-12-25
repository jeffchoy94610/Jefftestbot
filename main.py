import time
import random
import datetime
import pytz
import telepot
import telepot.namedtuple
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
import random
import _mysql
import pymysql
import urllib
import requests
import json

from config import *

def google(commandonly, querytype, querytext, chat_id, msgid):
    if commandonly == 1:
         bot.sendMessage(chat_id, "Please use `!gg <QUERY>` to search.", reply_to_message_id=reply_to, parse_mode='Markdown')
         return
    url = "https://www.googleapis.com/customsearch/v1?"
    apikey = GOOGLE_API
    cseid = CSE_ID
    url += "key=" + apikey
    url += "&cx=" +  CSE_ID
    url += "&q=" + urllib.parse.quote(querytext)
    if querytype == 'text':
        print("Searching text")
    elif querytype == 'image':
        print("Searching image")
        url += "&searchType=image"
#    url = url.replace(" ", "%20")
#    url = url.replace(",", "%2C")
    print(url)
    response = requests.get(url)
    result = response.json()
#    print(result)
    s_title = result['items'][0]['title']
    s_link = result['items'][0]['link']
    gmsg = "Search Result for <code>%s</code>:\n" % querytext
    gmsg += "<code>%s</code>\n" % s_title
    gmsg += "<a href='%s'>Click here</a>" % s_link
    print(gmsg)
    bot.sendMessage(chat_id, gmsg, reply_to_message_id=msgid, parse_mode='HTML', disable_web_page_preview='True')
    
def checkbanned(from_id):
    from_id =int(from_id)
    bansql = "select banned from user where telegramid=%d" % from_id
    cursor.execute(bansql)
    try:
        banned = cursor.fetchall()
        for row in banned:
            ban = row[0]
        db2.commit()
        return ban
    except:
        return -1

def jban(chat_id, msgid, banid):
    banid = int(banid)
    if checkbanned(banid) == 1:
        bot.sendMessage(chat_id, "User banned already", reply_to_message_id=msgid)
    elif checkbanned(banid) == -1:
        bot.sendMessage(chat_id, "ID wrong", reply_to_message_id=msgid)
    else:
        bannow = "update user set banned=1 where telegramid=%d" % banid
        try:
            cursor.execute(bannow)
            db2.commit()
            bot.sendMessage(chat_id, "Ban successful", reply_to_message_id=msgid)
        except:
            bot.sendMessage(chat_id, "Failed. Try again.", reply_to_message_id=msgid)

def junban(chat_id, msgid, unbanid):
    unbanid = int(unbanid)
    if checkbanned(unbanid) == 0:
        bot.sendMessage(chat_id, "User was not banned", reply_to_message_id=msgid)
    elif checkbanned(unbanid) == -1:
        bot.sendMessage(chat_id, "ID wrong", reply_to_message_id=msgid)
    else:
        unbannow = "update user set banned=0 where telegramid=%d" % unbanid
        try:
            cursor.execute(unbannow)
            db2.commit()
            bot.sendMessage(chat_id, "Unban Successful", reply_to_message_id=msgid)
        except:
            bot.sendMessage(chat_id, "Failed. Try again.", reply_to_message_id=msgid)

def jbanlist(chat_id, msgid):
    banlistsql = "select name, username, telegramid from user where banned=1"
    cursor.execute(banlistsql)
    db2.commit()
    result=cursor.fetchone()
    sqlmsg = "Banned users:\n"
    if result == None:
        sqlmsg  = "No banned users"
    while result is not None:
        sqlmsg+="`"+str(result)+"`\n"
        result=cursor.fetchone()
    bot.sendMessage(chat_id, sqlmsg, reply_to_message_id=msgid, parse_mode='Markdown')

def nopm(chat_id, from_user, msgid):
    nopmmsg = from_user + ", Please start me at PM first."
    buttontext = "Click to Start Me!"
    callbacktext = "start"
    bot.sendMessage(chat_id, nopmmsg, reply_to_message_id=msgid, reply_markup=button(buttontext, callbacktext))

def button(buttontext, callbacktext):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=buttontext, callback_data=callbacktext)]])
    return keyboard

def on_callback_query(msg):
    query_id, from_id, query_data = telepot.glance(msg, flavor='callback_query')
    if query_data == 'start':
        starturl="telegram.me/" + BOT_USERNAME + "?start=help"
        bot.answerCallbackQuery(query_id, url=starturl)

def help(chat_type, from_id, chat_id, reply_to, from_user, msgid):
        helpmsg = "Availble Commands:\n"
        helpmsg += "`/pat: [single use or by reply], pats someone`\n"
        helpmsg += "`/patstat: chat your pat history`\n"
        helpmsg += "`/myloc <location>: set your current location for using /now`\n"
        helpmsg += "`/now (<location>): return current weather for your already set location (or inputted location)`\n"
        helpmsg += "`/feedback <message>: send feedback to me!`\n"
        helpmsg += "`/gg <query>: search google, returns first result`"
        try:
            bot.sendMessage(from_id, helpmsg, parse_mode='Markdown')
            if chat_type != 'private':
                bot.sendMessage(chat_id, "I've sent you the help message in private.", reply_to_message_id=reply_to)
        except:
            if chat_type != 'private':
                nopm(chat_id, from_user, msgid)

def handle(msg):
    msg2 = telepot.namedtuple.Message(**msg)
    chat_id = msg['chat']['id']
    chat_id2 = msg2.chat.id
    chat_type = msg['chat']['type']
    command2 = msg2.text
    if command2 == None:
        return
    else:
        command = command2
    from_user = msg['from']['first_name']
    from_user2 = msg2.from_.first_name
    from_id = msg['from']['id']
    from_id2 = msg2.from_.id
    from_username2 = msg2.from_.username
    if from_username2 == None:
        from_username = None
        nousername = 1
    else:
        from_username = from_username2
        nousername = 0
    msgid = msg['message_id']
    msgid2 = msg2.message_id
    reply_to = msgid
    reply_to2 = msg2.message_id
    patcount = 0
    patdesc = "is patted defaultly by"
    to_user = 'None'

    if command[:1] == '/':
        using = '/'
    elif command[:1] == '!':
        using = '!'
    else:
        return

    db2 = pymysql.connect(MYSQL_SERVER, MYSQL_USERNAME, MYSQL_PW, MYSQL_DBNAME, charset='utf8')
    cursor = db2.cursor()
    cursor2 = db2.cursor()
    cursor.execute("set names utf8mb4")
    cursor.execute("set character set utf8mb4")
    cursor.execute("set character_set_connection=utf8mb4")

    bye = checkbanned(from_id)
    if bye == 1:
        return

    try:
        if chat_type == 'group' or chat_type == 'supergroup':
            group_id = chat_id
            group_name = db2.escape_string(msg['chat']['title'])
            checkgroupexist = "select * from `group` where groupid=%d" % group_id
            groupcount = cursor.execute(checkgroupexist)
            if groupcount == 0:
                newgroup = 1
                addgroup = "insert into `group` (`name`, `groupid`) values ('%s', %d)" % (group_name, group_id)
                cursor.execute(addgroup)
                db2.commit()
            else:
                newgroup = 0
                updategroup = "update `group` set name='%s' where groupid=%d" % (group_name, group_id)
                cursor.execute(updategroup)
                db2.commit()
    except:
        print("Add/Update Group error")
    try:
        usersql = "select * from user where telegramid=%d" % from_id
        userexist = cursor.execute(usersql)
        from_user_e = db2.escape_string(from_user)
        if userexist == 0:
            newuser = 1
            if nousername == 1:
                adduser = "insert into user (`name`, `telegramid`) values ('%s', %d)" % (from_user_e, from_id)
            else:
                adduser =  "insert into user (`name`,  `username`, `telegramid`) values ('%s', '%s', %d)" % (from_user_e, from_username, from_id)
            cursor.execute(adduser)
            db2.commit()
        else:
            newuser = 0
            if nousername == 1:
                updateuser = "update user set name='%s', username=None, where telegramid=%d" % (from_user_e, from_id)
            else:
                updateuser = "update user set name='%s', username='%s' where telegramid=%d" % (from_user_e, from_username, from_id)
            cursor.execute(updateuser)
            db2.commit()
    except:
        print("ERROR at add/update user")

    sql = "select count(patid) from patdb"
    try:
        cursor.execute(sql)
        data = cursor.fetchall()
        for row in data:
            patcount = row[0]
    except:
        print("ERROR at count pat desc")

    patnum = random.randint(1, patcount)

    sql2 = "select patdesc from patdb where patid = '%d'" % (patnum)
    try:
        cursor.execute(sql2)
        data = cursor.fetchall()
        for row in data:
            patdesc = row[0]
    except:
        print("ERROR")

    if msg2.reply_to_message == None:
        reply_to = msgid
    else:
        reply_to = msg['reply_to_message']['message_id']
        reply_to2 = msg2.reply_to_message
        to_user = msg['reply_to_message']['from']['first_name']
        to_user_id = msg['reply_to_message']['from']['id']
        to_user_username = msg['reply_to_message']['from']['username']
        try:
            checkreplyuserexist = "select * from user where telegramid=%d" % to_user_id
            rowcount=cursor.execute(checkreplyuserexist)
            to_user_e = db2.escape_string(to_user)
            if rowcount == 0:
                if nousername == 1:
                    addreplyuser = "insert into user (name, telegramid) values ('%s', %d)" % (to_user_e, to_user_id)
                else:
                    addreplyuser = "insert into user (name, username, telegramid) values ('%s', '%s', %d)" % (to_user_e, to_user_username, to_user_id)
                cursor.execute(addreplyuser)
                db2.commit()
            else:
                if nousername == 1:
                    editreplyuser = "update user set name='%s', username=None where telegramid=%d" % (to_user_e, to_user_id)
                else:
                    editreplyuser = "update user set name='%s', username='%s' where telegramid=%d" % (to_user_e, to_user_username, to_user_id)
                cursor.execute(editreplyuser)
                db2.commit()
        except:
            print("ERROR at add/edit reply user")
    
    if command[:1] == '/' or command[:1] == '!':
        multiple_args = command.split(' ')
        if len(multiple_args) > 1:
            commandonly = 0
            splitstring = command.split(' ', 1)
            after_command = splitstring[1]
            real_command = splitstring[0][1:]
            botusername = "@" + BOT_USERNAME
            if real_command[-13:] == botusername:
               real_command = real_command.split('@', 1)
               real_command = real_command[0]
               real_command = real_command.lower()
        else:
            commandonly = 1
            real_command = command[1:]
            real_command = real_command.split('@', 1)
            real_command = real_command[0]
            real_command = real_command.lower()
    else:
        real_command = 'NO'

    if real_command == 'NO':
        print('NOT COMMAND')
    else:
        if real_command == 'pat':
            patmsg = to_user
            patmsg += " "
            patmsg += patdesc
            patmsg += " "
            patmsg += from_user
            if to_user == 'None':
                bot.sendMessage(chat_id, '* pats pats *')
            else:
                bot.sendMessage(chat_id, patmsg, reply_to_message_id=reply_to)
                patcountadd=("update user set pattedby = (pattedby + 1) where telegramid=%d" % to_user_id)
                patbycountadd=("update user set patted = (patted + 1) where telegramid=%d" % from_id)
                try:
                    cursor.execute(patcountadd)
                    cursor.execute(patbycountadd)
                    db2.commit()
                except:
                    print("ERROR AT ADD PAT COUNT")
        elif real_command == 'start':
            if commandonly == 0:
                if after_command == 'help':
                    help(chat_type, from_id, chat_id, reply_to, from_user, msgid)
        elif real_command == 'myloc':
            if commandonly == 1:
                bot.sendMessage(chat_id, "Please use `/myloc <location>` to set your location.", reply_to_message_id=reply_to, parse_mode='Markdown')
                return
            setloc = db2.escape_string(after_command)
            setlocsql = "update user set loc='%s' where telegramid=%d" % (setloc, from_id)
            cursor.execute(setlocsql)
            db2.commit()
            setmsg = "Your location is set to `%s`" % setloc
            bot.sendMessage(chat_id, setmsg, reply_to_message_id=reply_to, parse_mode='Markdown')
        elif real_command == 'send':
            if from_id != ADMIN_ID:
                bot.sendMessage(chat_id, ("You are not %s!" % ADMIN_NAME), reply_to_message_id=reply_to)
                return
            if msg2.reply_to_message == None:
                if commandonly == 1:
                    bot.sendMessage(chat_id, "Use `!send <id> <message>`", reply_to_message_id=reply_to, parse_mode='Markdown')
                    return
                personplusmessage = after_command
                if len(personplusmessage.split(" ")) <= 1:
                    bot.sendMessage(chat_id, "Use `!send <id> <message>`", reply_to_message_id=reply_to, parse_mode='Markdown')
                    return
                splitpersonplusmessage = after_command.split(" ", 1)
                sendperson = splitpersonplusmessage[0]
                sendmessage = splitpersonplusmessage[1]
                if sendperson.isdigit():
                    try:
                        bot.sendMessage(sendperson, sendmessage)
                        bot.sendMessage(chat_id, "Message sent", reply_to_message_id=msgid)
                    except:
                        bot.sendMessage(chat_id, "Send Failed", reply_to_message_id=msgid)
                else:
                    sendperson = sendperson[1:]
                    personsql="select telegramid from user where username='%s'" % sendperson
                    cursor.execute(personsql)
                    db2.commit()
                    result = cursor.fetchall()
                    for row in result:
                        item = row[0]
                    db2.commit()
                    try:
                        bot.sendMessage(item, sendmessage)
                        bot.sendMessage(chat_id, "Message sent", reply_to_message_id=msgid)
                    except:
                        bot.sendMessage(chat_id, "Send Failed", reply_to_message_id=msgid)
            else:
                 sendperson = to_user_id
                 sendmessage = after_command
                 if reply_to2.forward_from != None:
                     sendperson = reply_to2.forward_from.id
                 try:
                     bot.sendMessage(sendperson, sendmessage)
                     bot.sendMessage(chat_id, "Message sent", reply_to_message_id=msgid)
                 except:
                     bot.sendMessage(chat_id, "Send Failed", reply_to_message_id=msgid)
        elif real_command == 'feedback':
            fbmessage = db2.escape_string(after_command)
            fbsql = "insert into feedback (message, name, username, telegramid) values ('%s', '%s', '%s', %d)" % (fbmessage, from_user, from_username, from_id)
            cursor.execute(fbsql)
            db2.commit()
            bot.sendMessage(chat_id, "Feedback sent!", reply_to_message_id=reply_to)
        elif real_command == 'help':
            help(chat_type, from_id, chat_id, reply_to, from_user, msgid)
        elif real_command == 'patstat':
            cursor2 = db2.cursor(pymysql.cursors.DictCursor)
            checkpatcount=("select patted, pattedby from user where telegramid=%d" % from_id)
            cursor2.execute(checkpatcount)
            patcount = cursor2.fetchall()
            for row in patcount:
               pats = row["patted"]
               patsby = row["pattedby"]
               patcountstr="Hello %s!\nYou have patted others `%d` times and got patted by others `%d` times." % (from_user, pats, patsby)
               bot.sendMessage(chat_id, patcountstr, reply_to_message_id=reply_to, parse_mode="Markdown")
        elif real_command == 'jsql':
            if from_id != ADMIN_ID:
                bot.sendMessage(chat_id, ("You are not %s!" % ADMIN_NAME), reply_to_message_id=reply_to)
                return
            try:
                enteredsql=after_command
                cursor.execute(enteredsql)
                db2.commit()
                result = cursor.fetchone()
                sqlmsg = "PERFORMING SQL QUERY:\n"
                while result is not None:
                   sqlmsg = sqlmsg + "`" + str(result) + "`"
                   sqlmsg = sqlmsg + "\n"
                   result = cursor.fetchone()
                sqlmsg = sqlmsg + "`num of affected rows: "+ str(cursor.rowcount) + "`"
                bot.sendMessage(chat_id, sqlmsg, reply_to_message_id=reply_to, parse_mode="Markdown")
            except pymysql.MySQLError as e:
                code, errormsg = e.args
                sqlerror = "`MySQL ErrorCode: %s\nErrorMsg: %s`" % (code, errormsg)
                bot.sendMessage(chat_id, sqlerror, reply_to_message_id=reply_to, parse_mode='Markdown')
        elif real_command == 'now':
            try:
                 if commandonly == 1:
                     checkloc="select loc from user where telegramid=%d" % from_id
                     cursor.execute(checkloc)
                     db2.commit()
                     result = cursor.fetchall()
                     for row in result:
                         userloc = row[0]
                     db2.commit()
                     if userloc == None:
                         bot.sendMessage(chat_id, "Please use `!myloc <location>` to set default location or use `!now <location>`.", reply_to_message_id=reply_to, parse_mode='Markdown')
                         return
                     else:
                         after_command = userloc
                 url = "http://dataservice.accuweather.com/locations/v1/search"
                 ran = random.randint(0,1)
                 if ran == 0:
                     apikey = ACCU_API_1
                 else:
                     apikey = ACCU_API_2
                 url += "?apikey=" + apikey
                 url += "&q=" +  after_command
                 url = url.replace(" ", "%20")
                 url = url.replace(",", "%2C")
                 response = requests.get(url)
                 result = response.json()
                 locationkey = result[0]['Key']
                 place = result[0]['LocalizedName'] + ", " + result[0]['AdministrativeArea']['LocalizedName'] + ", " + result[0]['Country']['LocalizedName']
                 localtzname = result[0]['TimeZone']['Name']
                 localtz = pytz.timezone(localtzname)
                 local = str(datetime.datetime.now(localtz))
                 url = "http://dataservice.accuweather.com/currentconditions/v1/"
                 url += locationkey
                 url += "?apikey=" + apikey
                 response = requests.get(url)
                 result = response.json()
                 localdate = local.split(" ", 1)[0]
                 localtimeandzone = local.split(" ", 1)[1]
                 localtime = localtimeandzone[:8]
                 localzone = localtimeandzone[-6:]
                 weather = result[0]['WeatherText']
                 ctemp = str(result[0]['Temperature']['Metric']['Value']) + "°" + result[0]['Temperature']['Metric']['Unit']
                 ftemp = str(result[0]['Temperature']['Imperial']['Value']) + "°" + result[0]['Temperature']['Imperial']['Unit']
                 wmsg = "Currently at: %s" % place
                 wmsg += "\nTemperature:`\t%s or %s`" % (ctemp, ftemp)
                 wmsg += "\nDescription:`\t%s`" % weather
                 wmsg += "\nLocal Time:`\t%s (UTC%s)`" % (localtime, localzone)
                 bot.sendMessage(chat_id, wmsg, reply_to_message_id=reply_to, parse_mode='Markdown')
            except:
                print("LOL")
                bot.sendMessage(chat_id, "Something wrong with your location...", reply_to_message_id=reply_to)
        elif real_command == 'jban':
            if from_id != ADMIN_ID:
                bot.sendMessage(chat_id, "You are not %s!" % ADMIN_NAME, reply_to_message_id=msgid)
                return
            if commandonly == 1:
                bot.sendMessage(chat_id, "Use `!jban <id>`", reply_to_message_id=msgid, parse_mode='Markdown')
                return
            if after_command.isdigit():
                jban(chat_id, msgid, after_command)
            else:
                bot.sendMessage(chat_id, "Not a valid id", reply_to_message_id=msgid)
                return
        elif real_command == 'junban':
            if from_id != ADMIN_ID:
                bot.sendMessage(chat_id, "You are not %s!" % ADMIN_NAME, reply_to_message_id=msgid)
                return
            if commandonly == 1:
                bot.sendMessage(chat_id, "Use `!junban <id>`", reply_to_message_id=msgid, parse_mode='Markdown')
                return
            if after_command.isdigit():
                junban(chat_id, msgid, after_command)
            else:
                bot.sendMessage(chat_id, "Not a valid id", reply_to_message_id=msgid)
                return
        elif real_command == 'jbanlist':
            if from_id != ADMIN_ID:
                bot.sendMessage(chat_id, "You are not %s!" % ADMIN_NAME, reply_to_message_id=msgid)
                return
            if commandonly == 1:
                jbanlist(chat_id, msgid)
        elif real_command == 'gg':
            google(commandonly, 'text', after_command, chat_id, msgid)

    db2.close()
    printmsg = "New Command '%s%s' from '%s (%d)'" % (using, real_command, from_user, from_id)
    printmsg += "\n"
    printmsg += "Chat type: '%s'\t" % chat_type
    if chat_type != 'private':
        if newgroup == 1:
            printmsg += 'NEW '
        printmsg += "Group: %s (%d)" % (group_name, group_id)
    printmsg += "\n"
    if commandonly == 0:
        printmsg += "After Command:\t%s\n" % after_command
    tz = pytz.timezone(ADMIN_TIMEZONE)
    timenow = str(datetime.datetime.now(tz))
    printmsg = timenow + "\n" + printmsg
    print(printmsg)
    with open("log.txt", "a") as logging:
        logging.write(printmsg + "\n")


bot = telepot.Bot(BOT_TOKEN)
db2 = pymysql.connect(MYSQL_SERVER, MYSQL_USERNAME, MYSQL_PW, MYSQL_DBNAME, charset='utf8')
cursor = db2.cursor()

def main():
    cursor.execute("set names utf8mb4")
    cursor.execute("set character set utf8mb4")
    cursor.execute("set character_set_connection=utf8mb4")

    cursor.execute(SQL_CREATE_TABLE_1)
    cursor.execute(SQL_CREATE_TABLE_2)
    cursor.execute(SQL_CREATE_TABLE_3)
    cursor.execute(SQL_CREATE_TABLE_4)
    db2.commit()
    try:
        cursor.execute(SQL_DEFAULT_PAT)
        db2.commit()
        db2.close()
    except:
        print("Default Pat String exists already.")
    bot.message_loop({'chat': handle, 'callback_query': on_callback_query})
    print('Initiating... Start fetching messages from telegram...\n')

    while 1:
        time.sleep(10)

main()
