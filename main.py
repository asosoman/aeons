#utf-8
import logging
import urwid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("aeon")
fh = logging.FileHandler("aeon.log")
fh.setLevel(logging.INFO)
logger.addHandler(fh)
logger.info("Inici")

CMONSTER = 0
CPLAYER = 1
CBUY = 2
PTSPELLS = 5
PTPLAY = 6
PTEND = 7
MTSPELLS = 8
MTEND = 9


class Card():
    def __init__(self, name):
        if name in list_cards.keys():
            self.cost = list_cards[name][0]
            self.name = name
            self.action = list_cards[name][1]
            self.owner = None
        else:
            self.cost = 0
            self.name = "TEST"
            self.action = Action("NONE",spark)
            self.owner = None
    def __str__(self):
        return " Cost: {} -- Name: {} -- Action: {}".format(self.cost, self.name, self.action)
    def __call__(self):
        self.action.act(self)

class Action():
    def __init__(self, txt, act):
        self.txt = txt
        self.act = act
    def __str__(self):
        return "{}".format(self.txt)

class Breach():
    status_list = [(1, None, None), (0, 2, 0), (0, 4, 2), (0, 6, 2), (0, 9, 3)]
    def __init__(self, player, status):
        if status not in (0, 1, 2, 3, 4):
            log("No valid value")
        else:
            self.spell = None
            self.player = player
            self.status = None
            self.open = None
            self.costOpen = None
            self.costTurn = None
            self.opentmp = None
            self.change_status(status)
    def __str__(self):
        txt = ""
        if self.open or self.opentmp:
            if self.spell:
                txt += "Spell: {}".format(self.spell.name)
            else:
                txt += "Spell: -----"
        if self.open:
            txt += "\n\nOpened Breach"
        else:
            txt += "\nOpen Breach: {} aether\nTurn Breach: {} aether".format(self.costOpen, self.costTurn)
        return txt
    def change_status(self, status):
        self.status = status
        self.open = self.status_list[status][0]
        self.costOpen = self.status_list[status][1]
        self.costTurn = self.status_list[status][2]
    def turn(self):
        if status and self.player.aether >= self.costTurn:
            self.change_status(self.status - 1)
            self.player.aether -= self.costTurn
            self.opentmp = 1
        else:
            log("Already opened")
    def open(self):
        if status and self.player.aether >= self.costOpen:
            self.change_status(0)
            self.player.aether -= self.costTurn
        else:
            log("Already opened")
    def set_spell(self, c):
        if self.open or self.opentmp:
            if self.spell is None:
                self.spell = c
            else:
                log("Already an spell on this breach!")
        else:
            log("Breach not opened!")
    def end_turn(self):
        self.opentmp = 0
    def play(self):
        self.spell()
        self.player.pdiscard(add(self.spell))
        self.spell = None
    def u(self):
        l = []
        b = urwid.Button
        t = urwid.Text
        if self.spell:
            l.append(t("Spell: {}".format(self.spell.name)))
        else:
            l.append(t("Spell: -------"))
        if self.open:
            l.append(t("Opened Breach"))
            return urwid.AttrMap(urwid.Filler(urwid.Pile(l),'top'),'opened')

        else:
            l.append(b("Open: {} Ae".format(self.costOpen)))
            l.append(b("Turn: {} Ae".format(self.costTurn)))
            return urwid.Filler(urwid.Pile(l),'top')

class Player():
    def __init__(self, name):
        self.life = 10
        #Create Deck
        self.pdeck = Deck(self)
        for c in mages[name]['deck']:
            self.pdeck.add(Card(c))
        self.phand = Deck(self)
        for c in mages[name]['hand']:
            self.phand.add(Card(c))
        self.pdiscard = Deck(self)
        self.playZone = Deck(self)
        self.name = name
        self.aether = 0
        self.charges = 0
        self.maxCharges = mages[name]['charges']
        self.costCharges = 2
        self.world = None
        self.action = mages[name]['action']
        self.breaches = []
        for b in mages[name]['breaches']:
            log("Creating Breach status: {}".format(b))
            self.breaches.append(Breach(self,b))
    def play(self, idxCard):
        if len(self.phand) == 0:
            log("No cards in hand")
            return
        self.phand[idxCard]()
        log("Played card {}".format(self.phand[idxCard].name))
        self.playZone.add(self.phand.draw(idxCard))
    def bplay(self, b, idxCard):
        self.play(idxCard)
        self.world.loop.widget = self.world.u()
    def buy(self, deck):
        if len(deck) == 0:
            log("Empty deck!!!")
            return
        if self.aether >= deck[0].cost:
            self.aether -= deck[0].cost
            log("Acquired card: {}".format(deck[0].name))
            self.pdiscard.add(deck.draw())
        else:
            log("Not enough aether to buy it")
    def buyCharge(self):
        if self.aether >= self.costCharges and self.charges < self.maxCharges:
            self.aether -= 2
            self.charges += 1
            log("Acquired charge")
        else:
            log("Action not allowed")
    def endTurn(self):
        self.aether = 0
        for x in range(len(self.playZone)):
            self.pdiscard.add(self.playZone.draw())
        print(self.world)
        log("End of turn")
    def u(self):
        t = urwid.Text

        tmp = [ b.u() for b in self.breaches ]
        logger.debug(tmp)
        cb = urwid.Columns(tmp)
        i = urwid.ListBox([t("Name: {}".format(self.name)),
                           t("Life: {}".format(self.life)),
                           t("Aether: {}".format(self.aether)),
                           t("Charges: {}/{}  Cost: {}".format(self.charges, self.maxCharges, self.costCharges)),
                           t("Action: {}".format(self.action)),
                           t("Deck: {} cards".format(len(self.pdeck)))
                           ])
        p1 = urwid.Pile([self.playZone.u(), self.phand.u(self.bplay)])
        cp = urwid.Columns([("weight", 3, p1), (
        "weight", 1, urwid.LineBox(self.pdiscard.u_narrow(), title="{} cards".format(len(self.pdiscard))))])
        p = urwid.LineBox(urwid.Pile([(5 , cb), ("weight", 1, i), ("weight", 2, cp)]), title=self.name)
        return p

class Deck():
    def __init__(self, owner=None):
        self.lista_cartas = []
        self.player = owner
    def __getitem__(self, item):
        return self.lista_cartas[item]
    def __len__(self):
        return len(self.lista_cartas)
    def __str__(self):
        for x in self.lista_cartas:
            print(x)
        return ""
    def __iter__(self):
        return self.lista_cartas.__iter__()
    def add(self, card):
        card.owner = self.player
        self.lista_cartas.append(card)
    def draw(self, idx=None):
        if idx:
            return self.lista_cartas.pop(idx)
        else:
            return self.lista_cartas.pop()
    def shuffle(self):
        import random
        random.shuffle(self.lista_cartas)
    def u(self, f=None):
        l = []
        for idx, c in enumerate(self):
            if f:
                l.append(urwid.Button(str(c), f, idx))
            else:
                l.append(urwid.Button(str(c)))
        return urwid.ListBox(l)
    def u_narrow(self):
        l = []
        for c in self:
            l.append(urwid.Text(str(c.name)))
        return urwid.ListBox(l)

class Monster():
    def __init__(self):
        self.life = 50
        self.name = "Cthulhu pelut"
    def u(self):
        m = urwid.LineBox(urwid.Frame(urwid.Columns([])), title=self.name)
        return m

class World():
    def __init__(self):
        self.monster = None
        self.players = []
        self.buyzone = []
        self.name = "Prova"
        self.activePlayer = None
        self.allCards = {}
        self.log = urwid.ListBox([urwid.Text("")])
        self.status = CMONSTER
        for c in list_cards:
            self.allCards[c] = Card(c)
    def __str__(self):
        print("Life: {} Name: {}".format(self.monster.life, self.monster.name))
        print("\n")
        for idx, d in enumerate(self.buyzone):
            if len(d) == 0:
                print("{}".format(idx))
            else:
                tipus = d.lista_cartas[0]
                print("{} -> ({}) Cost: {} -- Name: {} -- Action: {}".format(idx + 1, len(d), tipus.cost, tipus.name,
                                                                             tipus.action.txt))
        print("\n")
        for p in self.players:
            print("Name: {} - Life: {}".format(p.name, p.life))
            print("Charges: {}/{}  Cost: {}".format(p.charges, p.maxCharges, p.costCharges))
            print("Deck: {} cards".format(len(p.pdeck)))
            print("Hand:")
            for idx, c in enumerate(p.phand):
                print(" {} -> {}".format(chr(idx + 97), c))
            print("Play Zone:")
            print(p.playZone)
            print("Discard:")
            print(p.pdiscard)
            print("Aether: {}".format(p.aether))
        return ""
    def addPlayer(self, name):
        p = Player(name)
        p.world = self
        self.players.append(p)
        log("Added player: {}".format(p.name))
    def baddPlayer(self, b, idx):
        if b.label == "OK":
            self.status = 2
        else:
            self.addPlayer(b.label)
        self.loop.widget = w.u()
        self.newGame(b)
    def setMonster(self, monster):
        self.monster = monster
        log("Added monster: {}".format(monster.name))
    def bsetMonster(self, b, idx):
        self.setMonster(Monster())
        self.status = 1
        self.loop.widget = w.u()
        self.newGame(b)
    def createBuyDeck(self, card):
        import copy
        d = Deck()
        for x in range(10):
            d.add(copy.deepcopy(card))
        self.buyzone.append(d)
        log("Created deck {} in the Buy zone".format(card.name))
    def bcreateBuyDeck(self, b, idx):
        if b.label == "OK":
            self.status = 3
        else:
            if len(self.buyzone) < 9:
                self.createBuyDeck(Card(list_cards[b.label]))
            else:
                self.status = 3
        self.loop.widget = w.u()
        self.newGame(b)
    def newGame(self, b):
        if self.status == CMONSTER:
            self.popup(['Ctulhu'], self.bsetMonster, title="Choose Monster",create=True)
        elif self.status == CPLAYER:
            self.popup([m for m in mages.keys() if m not in [p.name for p in self.players]] + ["OK"], self.baddPlayer, title="Add player {}".format(len(self.players)+1), create=True)
        elif self.status == CBUY:
            self.popup(list_cards.keys()+ ["OK"], self.bcreateBuyDeck, title="Choose Buy Decks", create=True)
    def main(self):

        palette = [
            ('banner', 'black', 'light gray'),
            ('streak', 'black', 'dark red'),
            ('opened', 'black', 'yellow'), ]
        menu = urwid.ListBox([urwid.Button("New Game", self.newGame)])
        self.loop = urwid.MainLoop(menu, palette,unhandled_input=self.basicInput)
        self.loop.run()
    def basicInput(self, key):
        if str(key) in ("Q", "q"):
            raise urwid.ExitMainLoop()
        elif str(key) in ("12345"):
            self.activePlayer.buy(w.buyzone[int(key) - 1])
        elif str(key) in ("zZ"):
            self.activePlayer.buyCharge()
        elif str(key) in ("abcde"):
            self.activePlayer.play(ord(key) - 97)
        elif str(key) in ("lL"):
            if self.loop.widget != w.log:
                self.loop.widget = urwid.Overlay(urwid.LineBox(w.log, title="Log"), w.u(), "center", ('relative', 60),
                                                 "middle", ('relative', 60))
                return
        elif str(key) in ("P", "p"):
            self.popup(self.activePlayer.phand, self.activePlayer.bplay)
            return
        else:
            pass
        self.loop.widget = w.u()
    def popup(self, choices, f, title = None, create=None):
        l = []
        for idx, c in enumerate(choices):
            button = urwid.Button(str(c))
            urwid.connect_signal(button, "click", f, idx)
            l.append(urwid.AttrMap(button, None, focus_map="reversed"))
        lb = urwid.LineBox(urwid.ListBox(urwid.SimpleFocusListWalker(l)),title=title)
        if create:
            self.loop.widget = urwid.Overlay(lb, urwid.SolidFill('\N{MEDIUM SHADE}'), "center", ('relative', 60),
                                             "middle", ('relative', 60))
        else:
            self.loop.widget = urwid.Overlay(lb, w.u(), "center", ('relative', 60), "middle", ('relative', 60))
    def u(self):
        lb = []
        for idx, d in enumerate(self.buyzone):
            if len(d) == 0:
                lb.append(urwid.Text("{} - Empty".format(idx)))
            else:
                tipus = d[0]
                lb.append(urwid.Text(
                    "{} -> ({}) Cost: {} -- Name: {} -- Action: {}".format(idx + 1, len(d), tipus.cost, tipus.name,
                                                                           tipus.action.txt)))
        lBuy = urwid.ListBox(lb)
        lp = []
        for p in self.players:
            lp.append(p.u())
        cPlayers = urwid.Columns(lp)
        bMonster = w.monster.u()
        full = urwid.Pile([("weight", 1, bMonster), (10, lBuy), ("weight", 2, cPlayers)])
        p = urwid.Columns([("weight", 4, full), ("weight", 1, w.log)])
        return p

def log(txt):
    w.log.body.contents.append(urwid.Text(txt))
    w.log.focus_position = len(w.log.body.contents) - 1
    # w.log.set_text(w.log.get_text()[0]+'\n'+str(txt))
def monsterDamage(monster, num):
    monster.life -= num
def playerDamage(player, num):
    player.life -= num
def modAether(player, num):
    player.aether += num
def crystal(carta):
    modAether(carta.owner, 1)
def spark(carta):
    monsterDamage(carta.owner.world.monster, 1)

list_cards = {"Crystal": [0, Action("Gain 1 Aether", crystal)],
              "Spark": [1, Action("Deal 1 damage", spark)]
              }

mages = {
    "Z'hana": {
        'hand': ['Crystal', 'Crystal', 'Crystal', 'Crystal', 'Eternal Ember'],
        'deck': ['Crystal', 'Crystal', 'Crystal', 'Crystal''Spark'],
        'breaches': [3, 2, 4],
        'charges': 5,
        'action': "sanctum_glyph"
    },
    "Malastar": {
        'hand': ['Crystal', 'Crystal', 'Crystal', 'Crystal', 'Immolate'],
        'deck': ['Crystal', 'Crystal', 'Crystal', 'Crystal', 'Crystal'],
        'breaches': [3, 4, 2],
        'charges': 6,
        'action': "gift_of_aether"
    },
    "Garu": {
        'hand': ['Crystal', 'Crystal', 'Crystal', 'Spark', 'Torch'],
        'deck': ['Crystal', 'Crystal', 'Crystal', 'Spark', 'Spark'],
        'breaches': [0, 3, 2, 2],
        'charges': 5,
        'action': "colossal_force"
    },
    "Reeve": {
        'hand': ['Crystal', 'Crystal', 'Spark', 'Spark', 'Obsidian Shard'],
        'deck': ['Crystal', 'Crystal', 'Crystal', 'Spark', 'Spark'],
        'breaches': [0, 1, 2, 1],
        'charges': 4,
        'action': "quelling_blade"
    }
}

w = World()
w.main()
