#utf-8
import logging
import urwid
import random
from urwid import Text as uT
from urwid import LineBox as uLineB
from urwid import Columns as uC
from urwid import Pile as uP
from urwid import AttrMap as uA
from urwid import ListBox as uLB
from urwid import Button as uB
from urwid import Filler as uF
from urwid import Padding as uPad

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("aeon")
fh = logging.FileHandler("aeon.log")
fh.setLevel(logging.DEBUG)
logger.addHandler(fh)
logger.info("Inici")

#Turn Status
CMONSTER = 0
CPLAYER = 1
CBUY = 2
CTURN = 3
PTSPELLS = 5
PTPLAY = 6
PTEND = 7
MTSPELLS = 8
MTEND = 9

#Other Constants
CTYPE = ["relic", "gem", "spell"]

class Card():
    def __init__(self, name):
        if name in all_cards:
            self.cost = all_cards[name][0]
            self.name = name
            self.action = all_cards[name][1]
            self.owner = None
            self.type = all_cards[name][2]
        else:
            self.cost = 0
            self.name = "TEST"
            self.action = Action("NONE",spark)
            self.owner = None
            self.type = ""

    def __str__(self):
        return " Cost: {} -- Name: {} -- Action: {}".format(self.cost, self.name, self.action)

    def __call__(self):
        self.action.act(self)



class MCard():
    def __init__(self, monster, name):
        if name in monster_cards['basic']:
            info = monster_cards['basic'][name]
        elif name in monster_cards['monster']:
            info = monster_cards[monster][name]
        else:
            info = [""]

        if info[0] == "attack":
            self.type = info[0]
            self.name = name
            self.action = info[1]
            self.owner = None
            self.life = None
            self.discard = None
        elif info[0] == "minion":
            self.type = info[0]
            self.name = name
            self.action = info[1]
            self.owner = None
            self.life = info[2]
            self.discard = None
        elif info[0] == "power":
            self.type = info[0]
            self.name = name
            self.power = info[1][0]
            self.action = info[1][1]
            self.discard = info[2]
            self.owner = None
        else:
            self.name = "TEST"
            self.action = Action("NONE",spark)
            self.owner = None
            self.type = ""

    def __str__(self):
        if self.type == "attack":
            return " Name: {} -- Action: {}".format(self.name, self.action)
        elif self.type == "power":
            return " Name: {} -- Power: {} --  Action: {} -- Discard: {}".format(self.name, self.power, self.action, self.discard)
        elif self.type == "minion":
            return " Life: {} -- Name: {} -- Action: {}".format(self.life, self.name, self.action)
        else:
            return "No CARD VISIBLE"

    def __call__(self):
        self.action.act(self)


class Action():
    def __init__(self, txt, act):
        self.txt = txt
        self.act = act

    def __str__(self):
        return "{}".format(self.txt)


class Deck():
    def __init__(self, owner=None):
        self.cards = []
        self.player = owner

    def __str__(self):
        for x in self.cards:
            print(x)
        return ""

    def __getitem__(self, item):
        return self.cards[item]

    def __iter__(self):
        return self.cards.__iter__()

    def __len__(self):
        return len(self.cards)

    def add(self, card):
        card.owner = self.player
        self.cards.append(card)

    def draw(self, idx=None):

        if idx is not None:
            log("Idx {}".format(idx))
            return self.cards.pop(idx)
        else:
            log("No Idx {}".format(idx))
            return self.cards.pop()

    def shuffle(self):
        import random
        random.shuffle(self.cards)

    def u(self, f=None):
        l = []
        for idx, c in enumerate(self):
            if f:
                l.append(uB(str(c), f, idx))
            else:
                l.append(uB(str(c)))
        return uLB(urwid.SimpleFocusListWalker(l))

    def u_narrow(self):
        l = []
        for c in self:
            l.append(uT(str(c.name)))
        return uLB(l)


class Breach():
    status_list = [(1, 0, 0), (0, 2, 0), (0, 4, 2), (0, 6, 2), (0, 9, 3)]

    def __init__(self, player, status):
        if status not in (0, 1, 2, 3, 4):
            log("No valid value")
        else:
            self.spell = None
            self.player = player
            self.status = None
            self.opened = 0
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
        self.opened = self.status_list[status][0]
        self.costOpen = self.status_list[status][1]
        self.costTurn = self.status_list[status][2]

    def end_turn(self):
            self.opentmp = 0

    def open(self):
        if self.status and self.player.aether >= self.costOpen:
            self.player.aether -= self.costOpen
            self.change_status(0)
        else:
            if self.status: log("Not enough aether")
            else: log("Already opened")

    def open_(self, b):
        self.open()
        self.player.world.redraw()

    def play(self):
        self.spell()
        self.player.pdiscard.add(self.spell)
        self.spell = None

    def turn(self):
        if self.status and self.player.aether >= self.costTurn:
            self.player.aether -= self.costTurn
            self.change_status(self.status - 1)
            self.opentmp = 1
        else:
            if self.status: log("Not enough aether")
            else: log("Already opened")

    def turn_(self, b):
        self.turn()
        self.player.world.redraw()

    def set_spell(self, c):
        if self.opened or self.opentmp:
            if self.spell is None:
                self.spell = c
            else:
                log("Already an spell on this breach!")
        else:
            log("Breach not opened!")

    def u(self):
        l = []
        if self.spell:
            l.append(uT("Spell: {}".format(self.spell.name)))
        else:
            l.append(uT("Spell: -------"))
        if self.opened:
            l.append(uT("Opened Breach"))
            return uA(uF(uP(l),'top'),'opened')

        else:
            l.append(uB("Open: {} Ae".format(self.costOpen), self.open_))
            l.append(uB("Turn: {} Ae".format(self.costTurn), self.turn_))
            return uPad(uF(uP(l),'top'),left=1,right=1)


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

    def buy_(self, b, d):
        self.buy(d)
        self.world.redraw()

    def buyCharge(self):
        if self.aether >= self.costCharges and self.charges < self.maxCharges:
            self.aether -= 2
            self.charges += 1
            log("Acquired charge")
        else:
            log("Action not allowed")

    def buyCharge_(self, b):
        self.buyCharge()
        self.world.redraw()

    def end_turn(self):
        self.aether = 0
        for x in range(len(self.playZone)):
            self.pdiscard.add(self.playZone.draw())
        for x in range(5-len(self.phand)):
            if len(self.pdeck) == 0:
                log("Discard to deck")
                for y in range(len(self.pdiscard)):
                    self.pdeck.add(self.pdiscard.draw())
            self.phand.add(self.pdeck.draw())
        log("End of turn {}".format(self.name))

    def play(self, idxCard):
        if len(self.phand) == 0:
            log("No cards in hand")
            return
        if self.phand[idxCard].type == "spell":
            self.breaches[0].set_spell(self.phand[idxCard])
        else:
            self.phand[idxCard]()
            card_hand = self.phand.draw(idxCard)
            self.playZone.add(card_hand)
        log("Played card {}".format(self.phand[idxCard].name))
        return

    def play_(self, b, idxCard):
        one_choice = isinstance(self.phand[idxCard].action.txt,str)
        self.play(idxCard)
        if one_choice: self.world.redraw()

    def play_breach(self,b,idx):
        if b.label == "OK":
            self.world.status = PTPLAY
        else:
            self.breaches[0].play()
        self.world.redraw()

    def play_spells(self):
        l = []
        for idx,b in enumerate(self.breaches):
            if b.spell is not None:
                l.append(b.spell.name)
        if l:
            self.world.popup(l + ['OK'], self.play_breach, title="Spells to Play")
        else:
            self.world.status = PTPLAY
            self.world.redraw()

    def u(self):
        cb = uC([ b.u() for b in self.breaches ])
        i = uLB(urwid.SimpleFocusListWalker([
                           uT("Name: {}".format(self.name)),
                           uT("Life: {}".format(self.life)),
                           uT("Aether: {}".format(self.aether)),
                           uT("Charges: {}/{}  Cost: {}".format(self.charges, self.maxCharges, self.costCharges)),
                           uT("Action: {}".format(self.action)),
                           uT("Deck: {} cards".format(len(self.pdeck)))
                            ])
        )
        p1 = uP([self.playZone.u(), self.phand.u(self.play_)])
        cp = uC([("weight", 3, p1),
                 ("weight", 1, uLineB(self.pdiscard.u_narrow(), title="{} cards".format(len(self.pdiscard))))])
        p = uLineB(uA(uP([(5 , cb), ("weight", 1, i), ("weight", 2, cp)]),"default"), title=self.name)
        return p


class Monster():
    def __init__(self):
        self.life = 50
        self.name = "Cthulhu pelut"
        self.world = None
        self.deck = Deck(self)
        self.playzone = Deck(self)
        self.discard = Deck(self)

    def activate(self):
        for c in self.playzone:
            log("Playing {}".format(c.name))
            c()

    def end_turn(self):
        log("End of turn {}".format(self.name))

    def u(self):
        mc = uC([
            ('weight',2,uT(str(self.world.turn_order))),
            ('weight', 10, uP([(500,self.deck.u())])),
            urwid.Padding(urwid.BigText(str(self.life), urwid.font.HalfBlock5x4Font()), 'right', width='clip',right=1),
        ])
        m = uLineB(uA(uF(mc),'default'), title=self.name)
        return m


class World():
    def __init__(self):
        self.monster = None
        self.players = []
        self.buyzone = []
        self.name = "Prova"
        self.activePlayer = None
        self.allCards = {}
        self.log = uLB([uT("")])
        self.status = CMONSTER
        self.turn_order = []
        self.gravehold = 30
        for c in all_cards:
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
        log("Added player: {}".format(name))
        p = Player(name)
        p.world = self
        self.players.append(p)
        if len(self.players) == 1:
            self.activePlayer = p

    def baddPlayer(self, b, idx):
        if b.label == "OK":
            self.status = 2
        else:
            self.addPlayer(b.label)
        self.loop.widget = w.u()
        self.newGame(b)

    def basicInput(self, key):
        """

        :param key:
        :return:
        """

        if str(key) in ("Q", "q"):
            raise urwid.ExitMainLoop()
        elif str(key) in ("12345"):
            self.activePlayer.buy_(None, w.buyzone[int(key) - 1])
        elif str(key) in ("A"):
            self.activePlayer.end_turn()
            self.next_turn()
        elif str(key) in ("zZ"):
            self.activePlayer.buyCharge_(None)
        elif str(key) in ("abcde"):
            self.activePlayer.play_(None, ord(key) - 97)
        elif str(key) in ("lL"):
            if isinstance(self.loop.widget,uC):
                self.loop.widget = urwid.Overlay(uLineB(w.log, title="Log"), w.u(),
                                                 "center", ('relative', 60),
                                                 "middle", ('relative', 60))
                return
            else:
                self.redraw()
        else:
            return

    def create_turn(self):
        log("Players {}".format(len(self.players)))
        turn_order_list = [
            [1, 1, 1, 1, 0, 0],
            [1, 1, 2, 2, 0, 0],
            [1, 2, 3, -1, 0, 0],
            [1, 2, 3, 4, 0, 0]
        ]
        random.shuffle(turn_order_list[len(self.players)-1])
        self.turn_order = list(turn_order_list[len(self.players)-1])

    def createBuyDeck(self, card):
        import copy
        d = Deck()
        for x in range(10):
            d.add(copy.deepcopy(card))
        self.buyzone.append(d)
        log("Created deck {} in the Buy zone".format(card.name))

    def createBuyDeck_(self, b, idx):
        if b.label == "OK":
            self.status = CTURN
        else:
            if len(self.buyzone) < 9:
                self.createBuyDeck(Card(b.label))
            else:
                self.status = CTURN
        self.loop.widget = w.u()
        self.newGame(b)

    def main(self):
        palette = [
            ('banner', 'black', 'light gray'),
            ('default', 'default', 'default'),
            ('active', 'yellow', 'default'),
            ('opened', 'black', 'yellow'), ]
        lb = uA(uLB([uB("New Game", self.newGame)]),"default")
        menu = uA(uLineB(lb),"active")
        bg = urwid.SolidFill('\N{MEDIUM SHADE}')
        self.loop = urwid.MainLoop(urwid.Overlay(menu, bg , "center", ('relative', 60), "middle", ('relative', 60)), palette,unhandled_input=self.basicInput)
        self.loop.run()

    def newGame(self, b):
        logging.info("STARTING NEW GAME - Status: {} - Button: {}".format(self.status,b.label))
        if self.status == CMONSTER:
            log("CMONSTER")
            self.popup(['Ctulhu'], self.setMonster_, title="Choose Monster", create=True)
        elif self.status == CPLAYER:
            log("CPLAYER")
            self.popup([m for m in mages.keys() if m not in [p.name for p in self.players]] + ["OK"], self.baddPlayer, title="Add player {}".format(len(self.players)+1), create=True)
        elif self.status == CBUY:
            log("CBUY")
            self.popup([c for c in all_cards.keys() if c not in [z.cards[0].name for z in self.buyzone]] + ["OK"], self.createBuyDeck_, title="Choose Buy Decks", create=True)
        elif self.status == CTURN:
            log("CTURN")
            self.create_turn()
            self.next_turn()
            self.redraw()

    def next_turn(self):
        if len(self.turn_order) ==0: self.create_turn()
        pos = self.turn_order.pop(0)
        log("Seguent jugador {}".format(pos))
        if pos == -1:
            # SELECCIONAR JUGADOR
            self.activePlayer = self.players[random.randrange(len(self.players))]
            self.status = PTSPELLS
        elif pos == 0:
            self.activePlayer = self.monster
            self.status = MTSPELLS
        else:
            self.activePlayer = self.players[pos-1]
            self.status = PTSPELLS
        self.redraw()

    def popup(self, choices, f, title = None, create=None):
        """
        :param choices: choices for the popup
        :param f: function to execute when a choice is clicked
        :param title: title for the popup
        :param create: True if during creation phase
        :return: True
        """
        l = []
        for idx, c in enumerate(choices):
            #urwid.connect_signal(button, "click", f, idx)
            l.append(uA(uB(str(c),f,idx), None, focus_map="reversed"))
        lb = uLineB(uLB(urwid.SimpleFocusListWalker(l)),title=title)
        if create:
            self.loop.widget = urwid.Overlay(lb, urwid.SolidFill('\N{MEDIUM SHADE}'), "center", ('relative', 60),
                                             "middle", ('relative', 60))
        else:
            self.loop.widget = urwid.Overlay(lb, w.u(), "center", ('relative', 60), "middle", ('relative', 60))
        return

    def redraw(self):
        log("Status: {}".format(self.status))
        if self.status == PTSPELLS:
            self.activePlayer.play_spells()
        else:
            self.loop.widget = w.u()

    def set_active_player(self,name):
        self.activePlayer = self.players[[p.name for p in self.players].index(name)]
        self.redraw()

    def setMonster(self, monster):
        self.monster = monster
        monster.world = self
        log("Added monster: {}".format(monster.name))

    def setMonster_(self, b, idx):
        self.setMonster(Monster())
        for c in monster_cards['basic']:
            self.monster.deck.add(MCard(self.monster,c))
        self.status = CPLAYER
        self.newGame(b)

    def u(self):
        lb, lp = [], []
        for idx, d in enumerate(self.buyzone):
            if len(d) == 0:
                lb.append(uT("{} - Empty".format(idx)))
            else:
                tipus = d[0]
                lb.append(uT(
                    "{} -> ({}) Cost: {} -- Name: {} -- Action: {}".format(idx + 1, len(d), tipus.cost, tipus.name,
                                                                           tipus.action.txt)))
        for p in self.players:
            lp.append(uA(p.u(),"active") if self.activePlayer == p else p.u())
        lBuy = uF(uT("NO BUY DECKS"),'middle') if len(lb) == 0 else uLB(lb)
        cPlayers = uF(uT("NO PLAYERS"),'middle') if len(lp) == 0 else uC(lp)
        bMonster = uF(uT("NO MONSTER"),'middle') if w.monster is None else (uA(w.monster.u(),'active') if w.monster == self.activePlayer else w.monster.u())
        full = uP([("weight", 1, bMonster), (10, lBuy), ("weight", 2, uLineB(cPlayers,title="Gravehold: {}".format(self.gravehold)))])
        p = uC([("weight", 4, full), ("weight", 1, w.log)])
        return p


def aphotic_sun(carta):
    unleash()
    unleash()
    ghdamage(2)

def crystal(carta):
    modAether(carta.owner, 1)

def ghdamage(w, damage):
    w.gravehold -= damage
    return

def log(txt):
    w.log.body.contents.append(uT(txt))
    w.log.focus_position = len(w.log.body.contents) - 1
    # w.log.set_text(w.log.get_text()[0]+'\n'+str(txt))

def mangleroot(carta):
    unleash()
    unleash()
    ghdamage(2)

def modAether(player, num):
    player.aether += num
    return

def monsterDamage(num):
    w.monster.life -= num
    return

def playerDamage(player, num):
    player.life -= num
    return

def smite(carta):
    unleash()
    unleash()
    ghdamage(2)

def spark(carta):
    monsterDamage(1)

def torch(carta):
    def torch_opt(b,idx):
        if idx == 0:
            monsterDamage(1)
        elif idx == 1:
            modAether(carta.owner, 1)
        carta.owner.world.redraw()
        return
    carta.owner.world.popup(carta.action.txt,torch_opt,title=carta.name)
    return

def unleash(carta):
    log("unleash")


all_cards = {"Crystal": [0, Action("Gain 1 Aether", crystal),"gem"],
              "Spark": [1, Action("Deal 1 damage", spark),"spell"],
              "Torch": [0, Action(['Deal 1 damage','Get 1 ae'],torch),"spell"],
              }

monster_cards = {
    "basic": { "Smite": ['attack',Action("Unleash twice.Gravehold suffers 2 damage.",smite)],
               "Aphotic Sun": ['power',(2,Action("Unleash. The player with the most charges suffers 3 damage and loses all of their charges",aphotic_sun)),
                               ("Spend 7 Ae","aphotic_sun_discard")],
               "Mangleroot": ['minion',Action("Gravehold suffers 3 damage. This minion suffers 2 damage",mangleroot), 12],
    }

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