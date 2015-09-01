import cPickle
import irc.bot
import markovify
import random
import re
import requests


from string import letters, digits, punctuation


class Command:
    def __init__(self, label):
        self.label = label

    def __call__(self, func):
        func.cmd_label = self.label
        return func

class Trigger:
    def __init__(self, pattern):
        self.pattern = pattern

    def __call__(self, func):
        func.trigger_pattern = self.pattern
        return func


class TestBot(irc.bot.SingleServerIRCBot):
    def __init__(self, channel, nickname, server, port=6667):
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)

        self.channel = channel

        with open('shake2.txt') as f:
            self.shakespeare = markovify.Text(f.read())

        self.commands = {}
        self.triggers = []
        self.register_stuff()


    def on_nicknameinuse(self, conn, e):
        conn.nick(conn.get_nickname() + "_")


    def on_welcome(self, conn, e):
        conn.join(self.channel)


    def on_privmsg(self, conn, e):
        msg = e.arguments[0]
        parts = msg.split(' ')
        self.do_command(e, e.source.nick, parts[0], parts[1:])


    def on_pubmsg(self, conn, e):
        msg = e.arguments[0]
        if msg.lower().startswith('!' + conn.get_nickname().lower()):
            parts = msg.split(' ')
            if len(parts) > 1:
                self.do_command(e, e.target, parts[1], parts[2:])
        else:
            for pattern, handler in self.triggers:
                if pattern.match(msg):
                    handler(e.source.nick, e.target, msg)

    
    @Trigger(r"^.*https?://[^\s]+.*$")
    def on_link(self, sender, channel, msg):
        links = re.findall(r"https?://[^\s]+", msg)
        for link in links:
            try:
                resp = requests.get(link).text
                title = re.search(r"<title>(.*)</title>", resp).groups()[0]
                okchars = letters + digits + punctuation + ' '
                title = ''.join(c for c in title if c in okchars).strip()
                self.privmsg(channel, '%s: %s' % (link, title))
            except:
                pass


    @Command("curse")
    def cmd_curse(self, sender, channel, cmd, args):
        """curse <nick>\nPut a curse on <nick>."""
        if len(args) > 0:
            victim = args[0]
        else:
            victim = sender

        with open('curses.txt', 'r') as f:
            curses = list(cPickle.load(f))
        curse = random.choice(curses)

        self.privmsg(channel, "%s: %s" % (victim, curse))


    @Command("help")
    def cmd_help(self, sender, channel, cmd, args):
        """You're already using it!"""
        if len(args) == 0:
            cmdlist = "commands: %s" % ', '.join(self.commands.keys())
            self.privmsg(channel, "Use help <command> to learn about a specific command.")
            self.privmsg(channel, cmdlist)
            return

        helpcmd = args[0]
        if helpcmd.lower() in self.commands:
            docs = self.commands[helpcmd.lower()].__doc__
            self.privmsg(channel, docs)


    @Command("hw")
    def cmd_hw(self, sender, channel, cmd, args):
        """hw\nA programming classic."""
        self.privmsg(channel, "hello world")


    @Command("shakespeare")
    def cmd_shakespeare(self, sender, channel, cmd, args):
        """shakespeare\nGenerate some classic literature.."""
        self.privmsg(channel, self.shakespeare.make_sentence())


    @Command("insult")
    def cmd_insult(self, sender, channel, cmd, args):
        """insult <nick>\nSay mean things to the user."""

        if len(args) > 0:
            victim = args[0]
        else:
            victim = sender

        insults = [
            "Fuck you, <nick>",
            "<nick> couldn't point out the Earth on a globe.",
            "<nick> couldn't pour water out of a boot if the instructions were written on the heel.",
            "\x01 bites thumb\x01\n<nick>: I do not bite my thumb at you sir; but I bite my thumb, sir.",
            "<nick> is a cotton-headed ninny muggins!",
            "<nick>: Your mother was a hamster, and your father smelt of elderberries!",
            "Hey <nick>, where did you get those clothes?At the.. toilet store?",
            "<nick> is at the top of the bell curve!",
        ]

        compliments = [
            "<nick> is the best!",
            "<nick> is the greatest!",
            ":)",
            "<nick> is awesome!",
            "<3 <nick>",
        ]

        if victim.lower() not in ['volbot', 'joecon']:
            insult = random.choice(insults).replace('<nick>', victim)
            self.privmsg(channel, insult)
        else:
            insult = random.choice(compliments).replace('<nick>', victim)
            self.privmsg(channel, insult)
            

    def do_command(self, e, target, cmd, args):
        nick = e.source.nick
        conn = self.connection

        if cmd.lower() in self.commands:
            handler = self.commands[cmd.lower()]
            handler(nick, target, cmd, args)
        else:
            self.privmsg(target, "what?")


    def register_stuff(self):
        for attr in dir(self):
            obj = getattr(self, attr)
            if hasattr(obj, "cmd_label"):
                label = getattr(obj, "cmd_label")
                print 'registered %s' % label
                self.commands[label.lower()] = obj
            elif hasattr(obj, "trigger_pattern"):
                pattern = getattr(obj, "trigger_pattern")
                print 'registered %s' % pattern
                self.triggers.append((re.compile(pattern), obj))


    def privmsg(self, target, msg):
        lines = msg.split('\n')
        for line in lines:
            self.connection.privmsg(target, line)


def main():
    import sys
    if len(sys.argv) != 4:
        print("Usage: testbot <server[:port]> <channel> <nickname>")
        sys.exit(1)

    s = sys.argv[1].split(":", 1)
    server = s[0]
    if len(s) == 2:
        try:
            port = int(s[1])
        except ValueError:
            print("Error: Erroneous port.")
            sys.exit(1)
    else:
        port = 6667
    channel = sys.argv[2]
    nickname = sys.argv[3]

    bot = TestBot(channel, nickname, server, port)
    bot.start()

if __name__ == "__main__":
    main()
