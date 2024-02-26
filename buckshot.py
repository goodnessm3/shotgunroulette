import random
from collections import defaultdict

ITEMS = ["cuff", "beer", "saw", "cigs", "glass"]
# other commands are sopp and sself for shoot opponent and self respectively
LIVES = 4
MIN_SIZE = 2
MAG_SIZE = 6
CIG_INCREMENT = 1  # how much cigs heal  you
PLIVES = 4
DLIVES = 4  # how many lives does each player start with


class Shotgun:

    def __init__(self, min_size=MIN_SIZE, mag_size=MAG_SIZE):

        self.mag = []
        self.mag_size = mag_size
        self.min_size = min_size

    def load(self):

        self.mag = []
        nm = random.randint(self.min_size, self.mag_size)
        for x in range(nm):
            self.mag.append(random.choice((True, False)))  # True = live shell
        return self.mag.count(True), self.mag.count(False)  # return distribution of contents

    def fire(self):

        return self.mag.pop()

    def peek(self):

        """Peek the next round to be fired using the magnifying glass"""

        return self.mag[-1]  # pop is from right so want the last element

    def is_empty(self):

        return len(self.mag) == 0

    def get_distribution(self):

        """Returns live, blank rounds"""

        return self.mag.count(True), self.mag.count(False)

    def live_probability(self):

        """Returns the probability that the shot was from a live shell"""

        lv = self.mag.count(True)
        blnk = self.mag.count(False)
        return float(lv/(lv + blnk))


class GameState:

    def __init__(self, plives=PLIVES, dlives=DLIVES, pitems=None, ditems=None, player_cuffed=False, dealer_cuffed=False,
                 gun_sawn=False, current_turn="PLAYER", opponent="DEALER", live_shells=0, blank_shells=0,
                 probability=0.0):

        self._player_lives = plives
        self._dealer_lives = dlives
        if pitems:
            self.player_items = pitems
        else:
            self.player_items = []
        if ditems:
            self.dealer_items = ditems
        else:
            self.dealer_items = []
        self.player_cuffed = player_cuffed
        self.dealer_cuffed = dealer_cuffed
        self.gun_sawn = gun_sawn
        self.finished = False
        self.winner = None
        self.loser = None
        self.current_turn = current_turn
        self.opponent = opponent

        # properties used in simulation. The game state knows how many of each shell are left, but nothing
        # about the order. So it's distinct from the gun object that has info about the order too.
        self.live_shells = live_shells
        self.blank_shells = blank_shells
        self.probability = probability  # updated when the AI makes this as a simulation
        self.label = ""  # for printing/debugging

    @property
    def player_lives(self):

        return self._player_lives

    @player_lives.setter
    def player_lives(self, a):

        self._player_lives = min(a, LIVES)

    @property
    def dealer_lives(self):

        return self._dealer_lives

    @dealer_lives.setter
    def dealer_lives(self, a):

        self._dealer_lives = min(a, LIVES)

    def live_probability(self):

        return float(self.live_shells)/(self.live_shells + self.blank_shells)

    def print(self):

        out = f"PROBABILITY: {self.probability} = {self.label} HEURISTIC: {self.heuristic()}\n"

        plist = ", ".join(self.player_items)
        dlist = ", ".join(self.dealer_items)

        out += (f"PLAYER: {self.player_lives} lives, items = {plist}\n"
                f"DEALER: {self.dealer_lives} lives, items =  {dlist}\n")

        out += f"GUN: {self.live_shells} live; {self.blank_shells} blank\n"
        out += f"CURRENT TURN: {self.current_turn}\n"
        if self.player_cuffed or self.dealer_cuffed:
            out += f"DEALER CUFFED: {self.dealer_cuffed}\n"
            out += f"PLAYER CUFFED: {self.player_cuffed}\n"
        if self.gun_sawn:
            out += "GUN SAWN"

        return out

    def get_copy(self):

        """Make a new GameState with copies of all attributes, for speculative purposes. Note use of [:]
        to get a copy of the list, rather than a reference to a list!"""

        return GameState(self.player_lives, self.dealer_lives, self.player_items[:], self.dealer_items[:],
                         self.player_cuffed, self.dealer_cuffed, self.gun_sawn, self.current_turn, self.opponent,
                         self.live_shells, self.blank_shells)

    def heuristic(self):

        """A score used to rank which course of action is the best"""

        def list_value():

            # TODO: determine optimum values
            valdc = {"glass": 0.008,
                     "cigs": 0.017,
                     "beer": 0.0105,
                     "cuff": 0.011,
                     "saw": 0.015}

            score = 0
            for q in self.dealer_items:
                score += valdc[q]

            return score

        sc = (self.dealer_lives * 1.05 - self.player_lives) * self.probability + list_value()
        # 1.05 factor slightly favours the dealer trying to stay alive with cigs etc

        if self.winner == "DEALER":
            sc += 100

        return sc


class GameRunner:

    """Collection of functions that take a command and apply it to the game state object to mutate it."""

    def __init__(self):

        self.func_dict = {
            "sself": self.shoot,
            "sopp": self.shoot,
            "cuff": self.cuff,
            "beer": self.beer,
            "saw": self.saw,
            "cigs": self.cigs,
            "glass": self.glass
        }

    def evaluate_command(self, state, cmd, live_shell):

        if state.current_turn == "PLAYER":
            actor = "PLAYER"
            opponent = "DEALER"
        else:
            actor = "DEALER"
            opponent = "PLAYER"

        # use the type of command to determine to whom it's applied

        if cmd == "sself":
            target = actor  # both of these map to the "shoot" command we only need to set the target
        elif cmd == "sopp":
            target = opponent  # both of these map to the "shoot" command we only need to set the target
        elif cmd == "cuff":
            target = opponent
            # one day may be able to cuff self but I don't see why it's useful
        elif cmd == "cigs":
            target = actor
        else:
            target = None  # targetless commands like saw, glass, beer

        self.func_dict[cmd](state, target, live_shell)  # lookup the function by name and apply it, update the state

        if cmd in ITEMS:
            if actor == "PLAYER":
                state.player_items.remove(cmd)  # remove the item from the inventory of player or dealer
            elif actor == "DEALER":
                state.dealer_items.remove(cmd)

    def cuff(self, state, target, live_shell):

        if target == "PLAYER":
            state.player_cuffed = True
        elif target == "DEALER":
            state.dealer_cuffed = True

    def saw(self, state, target, live_shell):

        state.gun_sawn = True

    def cigs(self, state, target, live_shell):

        if target == "PLAYER":
            state.player_lives += CIG_INCREMENT
        elif target == "DEALER":
            state.dealer_lives += CIG_INCREMENT

    def glass(self, state, target, live_shell):

        """Handled outside of this object. Nothing to do - doesn't change state."""

        pass

    def beer(self, state, target, live_shell):

        if live_shell:
            state.live_shells -= 1
        else:
            state.blank_shells -= 1

    def shoot(self, state, target, live_shell):

        # shoot the target, only a live round does anything. We do the live shell check here to avoid
        # having to do more complicated checks in the runner code that calls this idk it makes sense to me

        if live_shell:
            if state.gun_sawn:
                damage = 2
            else:
                damage = 1
            if target == "PLAYER":
                state.player_lives -= damage
            elif target == "DEALER":
                state.dealer_lives -= damage
            self.flip(state)  # shooting a live round always advances the player
            state.live_shells -= 1
        else:
            if not target == state.current_turn:
                self.flip(state)  # blank shell vs. other player, advances player
                # blank shell against yourself does NOT flip.
            state.blank_shells -= 1

        state.gun_sawn = False

    def check_game_over(self, state):

        """Checks if someone is dead and returns the name of the WINNER if so."""

        if state.player_lives < 1:
            state.finished = True
            state.winner = "DEALER"
            state.loser = "PLAYER"
            return "DEALER"
        elif state.dealer_lives < 1:
            state.finished = True
            state.winner = "PLAYER"
            state.loser = "DEALER"
            return "PLAYER"
        else:
            return

    def flip(self, state):

        if state.current_turn == "PLAYER":
            if state.dealer_cuffed:
                state.dealer_cuffed = False  # do nothing, but back to normal next time
            else:
                state.current_turn = "DEALER"
                state.opponent = "PLAYER"
        elif state.current_turn == "DEALER":
            if state.player_cuffed:
                state.player_cuffed = False
            else:
                state.current_turn = "PLAYER"
                state.opponent = "DEALER"


class Game:

    """The actual ongoing game that is happening, with one specific shotgun object. Does the logic to
    determine what came out of the shotgun, checks for game over conditions, etc. By keeping this
    divorced from the game state update machinery, we can use that machinery to make simulated states
    for the AI to explore its options by 'forcing' certain outcomes to explore exhaustively."""

    def __init__(self):

        self.messages = []  # accumulate messages to be printed each turn
        self.gun = Shotgun()
        self.game_state = GameState()  # instantiated with the default parameters i.e. player goes first etc
        self.game_runner = GameRunner()  # TODO: probably doesn't even need to be a class
        self.load_gun()

        for q in ITEMS:
            # TODO: temporary, some default items
            self.game_state.dealer_items.extend([q]*2)
            self.game_state.player_items.extend([q]*2)

        self.log(f"{self.game_state.current_turn}'s turn.")

    def load_gun(self):

        live, blank = self.gun.load()

        self.game_state.live_shells = live
        self.game_state.blank_shells = blank  # the game state also keeps track of the shells

        self.log(f"The gun is loaded with {live} live rounds and {blank} blanks in a random order.")

    def log(self, msg):

        self.messages.append(msg)

    def print_log(self):

        out = self.messages[:]
        self.messages = []
        return "\n".join(out)

    def update(self, cmd):

        """Send the cmd into the stored state object"""

        self.log(f"{self.game_state.current_turn} used {cmd}")

        shell = None  # replaced if the command actually involved firing the gun

        if self.game_state.gun_sawn:
            # this will be used by any shooting result that depends on whether the gun was sawn off
            dmg = 2
        else:
            dmg = 1

        if cmd == "sself":
            # find out what was in the gun
            shell = self.gun.fire()
            if shell:
                self.log(f"{self.game_state.current_turn} shot themselves with a live shell for {dmg} damage.")
            else:
                self.log(f"A blank round. {self.game_state.current_turn} continues playing.")

        elif cmd == "sopp":
            shell = self.gun.fire()
            if shell:
                self.log(f"{self.game_state.current_turn} shot {self.game_state.opponent} for {dmg} damage.")
            else:
                self.log(f"{self.game_state.current_turn} shot {self.game_state.opponent} with a blank shell.")

        elif cmd == "glass":
            # this command doesn't do anything to the game state, but gives us a readout here instead.
            if self.gun.peek():
                self.log("You peeked a live round in the chamber.")
            else:
                self.log("You peeked a blank round in the chamber.")

        elif cmd == "beer":
            shell = self.gun.fire()
            if shell:
                self.log("A live round came out.")
            else:
                self.log("A blank round came out.")

        elif cmd == "cigs":
            self.log(f"{self.game_state.current_turn} smoked a cigarette to regain {CIG_INCREMENT} lives.")

        elif cmd == "cuff":
            self.log(f"{self.game_state.current_turn} used handcuffs and {self.game_state.opponent} misses their turn.")

        elif cmd == "saw":
            self.log(f"{self.game_state.current_turn} used the saw, shotgun deals double damage on next shot.")

        if self.game_state.player_cuffed:
            self.log("Player is handcuffed and will miss their next turn.")
        elif self.game_state.dealer_cuffed:
            self.log("Dealer is handcuffed and will miss their next turn.")

        # having logged what the command did, now we actually evaluate it and update the state object
        self.game_runner.evaluate_command(self.game_state, cmd, shell)

        if winner := self.game_runner.check_game_over(self.game_state):  # hehe, walrus operator :^)
            self.log(f"{winner} killed the {self.game_state.loser} and won the game!")
            return True

        if self.gun.is_empty():  # TODO: I moved this around to try and fix the error
            self.log("Gun is empty - reloading for the next round.")
            self.load_gun()

        self.log(f"{self.game_state.current_turn}'s turn.")


class AI:

    def __init__(self, game):

        self.game = game  # the game that is actually running, the gun belongs to this object
        self.game_runner = GameRunner()  # AI's own game runner to simulate actions

    def take_turn(self):

        opts = self.get_options()
        future_states = []
        heuristics = []  # work out how good each option is, we need to add two
        # heuristics together when it could go either way
        for i in opts:
            outcomes = self.create_state(self.game.game_state, i)  # a tuple of length 1 or 2
            goodness = 0
            for j in outcomes:
                goodness += j.heuristic()  # accumulate how good the options are
            heuristics.append((i, goodness))  # use this to ultimately pick what to do
            heuristics.sort(key=lambda m: m[1])  # sort by goodness score in tuple
            future_states.extend(outcomes)

        #print("HEURISTICS FOR POSSIBLE COMMANDS:")
        #for x, y in heuristics:
            #print(x, ": ", y)

        #for k in future_states:
            #print("Possible state:")
            #print(k.print())
            #print("++++++++++++++++++")

        return heuristics[-1][0]  # the command inside the tuple that was sorted the highest score

        '''
        live_prob = self.game.gun.live_probability()
        if live_prob > 0.5:
            print("### live prob > 0.5, shooting you")
            return "sopp"
        else:
            print("### live prob < 0.5, shooting myself")
            return "sself"
        '''

    def get_options(self):

        """All the things the AI can possibly do this turn."""

        out = ["sopp", "sself"] + self.game.game_state.dealer_items
        while "glass" in out:
            out.remove("glass")  # glass is not used in simulation, because it doesn't change anything

        return set(out)  # only evaluate each option once

    def create_state(self, state, cmd):

        """Use a command to modify the state object and see what the result would be. Returns a new
        state object having copied the original one, which is not mutated. Live_shell is True or False
        and is needed to decide whether to run a shooting function."""

        if cmd in ["sself", "sopp", "beer"]:  # these are the only commands that "branch"
            prob = state.live_probability()

            new_true = state.get_copy()
            self.game_runner.evaluate_command(new_true, cmd, True)
            new_true.probability = prob  # annotate the state with probability of occurrence
            new_true.label = f"Dealer used {cmd} with live shell"

            new_false = state.get_copy()
            self.game_runner.evaluate_command(new_false, cmd, False)
            new_false.probability = 1.0 - prob
            new_false.label = f"Dealer used {cmd} with blank shell"

            return new_true, new_false

        else:
            new = state.get_copy()
            self.game_runner.evaluate_command(new, cmd, None)  # live_shell arg does not matter for these cmds
            new.probability = 1.0  # no ambiguity, prob of success is 1
            new.label = f"Dealer used {cmd}"

            return new,  # tough guy way to make a 1-tuple, always want a tuple from this function


if __name__ == "__main__":

    gm = Game()
    trn = 1
    ai = AI(gm)

    while True:

        print("---")
        #print(gm.game_state.print())

        print(gm.print_log())
        print(f"TURN {trn}")
        #print("current gun mag: ", gm.gun.mag)
        #print("here is the game state now:")
        #print(gm.game_state.print())
        if gm.game_state.current_turn == "PLAYER":
            turn = input(">> ")
            print("============================")
            if turn == "q":
                print("Quitting")
                break
        else:
            turn = ai.take_turn()
        result = gm.update(turn)
        if result:
            print(gm.print_log())
            print("game ended!")
            break

        trn += 1
