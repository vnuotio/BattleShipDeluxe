"""
BATTLESHIP 2021 Deluxe Edition
COMP.CS.100 13.10 Graafinen käyttöliittymä
Tekijä: Vertti Nuotio
Opiskelijanumero: H300132
email: vertti.nuotio@tuni.fi

Työssä tähdättiin kehittyneeseen versioon projektista.

Tämä ohjelma luo yksinkertaisen graafisen käyttöliittymän laivanupotuspelille.
Ohjelman aluksi käyttäjältä kysytään pelissä olevien laivojen lukumäärä sekä
käyttäjän ammuksien määrä, jonka jälkeen Continue-napin painalluksella peli avautuu.

Käyttäjällä on rajattu määrä ammuksia hallussaan, joiden loppuessa peli päättyy
tappioon. Kaikkien vihollislaivojen upottaminen johtaa voittoon.
Käyttäjä voi painaa mitä tahansa ruutua koordinaattiruudukolla, jolloin paljastuu,
onko hän osunut laivaan.
Laivan upotessa sekä pelin päättyessä aukeavat erilliset ikkunat, jotka kertovat
käyttäjälle tapahtumista.
"""

from tkinter import *
from tkinter import messagebox
from enum import Enum
import random
from sys import exit
from functools import partial

# region Global constants
IMAGE_FILEPATH = "imagefiles/"
IMAGE_FILES = {"Unknown": "unknown.gif", "Empty": "empty.gif", "Hit": "hit.gif", "Sunk": "sunk.gif"}

# Valid ship types and their lengths.
SHIPS = {"Battleship": 4, "Cruiser": 3, "Destroyer": 2, "Submarine": 1}

# Acceptable X-coordinates. If you want to scale the board up/down, this is
# all you need to change.
BOARD_X = ('A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J')

# Acceptable Y-coordinates, there are as many as X coordinates. Used by
# range() so that by default the min Y-coord is 0 and max is 9 (assuming BOARD_X = 'A'...'J').
BOARD_Y = len(BOARD_X)

# endregion


# region UI Elements
class Board:
    """
    Class representing individual boards, made of buttons.
    """

    def __init__(self, master, match_type, shell_amount):
        """
        :param master: master object of this board in the sense of tkinter windows / frames.
        """
        self.__master = master
        # <self.board> contains the buttons and images for what each tile should display.
        self.__board = {}
        # All of the ships on this board.
        self.__ships = []
        # Amount of shots the player has left before the game ends.
        self.__shots_available = shell_amount
        self.shot_counter = StringVar(value=f"Shots left: {self.__shots_available}")

        # contains PhotoImages of tile images.
        self.__board_images = {}
        # Checks if all files can be succesfully found.
        try:
            for img in IMAGE_FILES:
                self.__board_images[img] = PhotoImage(file=IMAGE_FILEPATH + IMAGE_FILES[img])
        except TclError:
            errorpopup(master, "Missing .gif files", "There are missing .gif files in your /imagefile/ folder!")

        # Create the tiles (Buttons) for each coordinate on the board.
        for ind_x, x in enumerate(BOARD_X):
            self.__board[x] = {}
            for y in range(BOARD_Y):
                self.__board[x][y] = Button(master,
                                            image=self.__board_images["Unknown"],
                                            command=partial(self.__shoot, x, y))
                self.__board[x][y].grid(row=y, column=ind_x)

        # Creation of ships for the board.
        for i in range(match_type):
            new_ship = generate_ship(self.__ships)
            self.__ships.append(new_ship)

    def __shoot(self, x, y):
        """
        Called when a tile (Button) on a Board is clicked (if it hasn't been clicked before).
        Checks if any ship is on that tile, then disables that button and assigns a correct
        image to the tile based on there being a ship or not.
        :param x: string, the character indicating X position (column)
        :param y: int, the number indicating Y position (row)
        """
        # -1 shell away...
        self.__shots_available -= 1
        self.shot_counter.set(value=f"Shots left: {self.__shots_available}")

        # Coordinate we shot at in string form.
        self.__coord = x + str(y)
        # Check if we hit anything.
        self.__hit_ship = in_ship_coordinates(self.__ships, self.__coord)

        # Didn't hit anything
        if self.__hit_ship is None:
            self.__board[x][y].configure(command="", image=self.__board_images["Empty"])
        # Hit...
        else:
            self.__hit_ship.hit_parts += 1
            # ...and sank!
            # If we have hit this ship as many times as its length, sink it.
            if self.__hit_ship.hit_parts == SHIPS[self.__hit_ship.ship_type]:
                # Change the image on every tile of this ship to sunken.
                for c in self.__hit_ship.coordinates:
                    x = c[0]
                    y = int(c[1])
                    self.__board[x][y].configure(command="", image=self.__board_images["Sunk"])
                self.__ships.remove(self.__hit_ship)

                # We sank a ship!
                messagebox.showinfo(title="Critical hit on enemy ship!",
                                    message="We can see plumes of smoke over the horizon!"
                                            f" Looks like we sank a {self.__hit_ship.ship_type}!")

                # All ships have been sunk! We are victorious!
                if len(self.__ships) <= 0:
                    self.__game_over("We are victorious!", "Enemy guns have fallen silent, and"
                                                           " our scout planes see only burning wrecks."
                                                           " It seems we sank them all!")

            # ...but didn't sink.
            else:
                self.__board[x][y].configure(command="", image=self.__board_images["Hit"])

        # Game defeat condition. If the player wins, this condition will never even be tested for.
        if self.__shots_available <= 0:
            self.__game_over("Retreat...", "Our ships have ran out of shells, and we have no option"
                                           " but to retreat...")

    def __game_over(self, title, msg):
        self.__restart_command = messagebox.askyesno(title=title, message=msg + "\nNew game?")

        # Restart game
        if self.__restart_command:
            # Closes the main Tk() instance, then restarts the program.
            self.__master.master.master.destroy()
            main()
        # Exit the program
        else:
            exit()


class Ship:
    """
    The class representing Ship objects. Each ship has a string <ship_type>, dict <coordinates>
    and int <hit_parts>.
    """
    def __init__(self, ship_type, coordinates):
        """
        :param ship_type: string, ship type - battleship, cruiser, destroyer, submarine etc.
        Any string is valid.
        :param coordinates: list of strings, marking every coordinate this ship occupies.
        """
        self.ship_type = ship_type
        self.coordinates = coordinates
        # Represents how many times this hit has been hit(a single position can be hit only once).
        self.hit_parts = 0


class RuleSetupGUI:
    """
    Handles the Match Type selection screen.
    """
    def __init__(self):
        self.continue_setup_bool = False
        # Main window
        self.__root = Tk()
        self.__root.title("BATTLESHIP 2021 Deluxe Edition")
        self.__root.geometry("320x160")

        # region ROW 0
        # Explanation label
        Label(self.__root, text="Select the match type: Amount of enemy ships.").grid(row=0, columnspan=len(MatchType))
        # endregion

        # region ROW 1
        # Radiobuttons for match type
        self.match_type = IntVar()
        for c, option in enumerate(MatchType):
            self.__button_text = f"{option.name.capitalize()}({option.value})"
            Radiobutton(self.__root, text=self.__button_text, var=self.match_type, value=option.value).grid(row=1, column=c)
            self.__root.columnconfigure(c, weight=1)
        # endregion

        # region ROW 2
        # Maximum amount of shots the player has available for the game before it ends.
        Label(self.__root, text="Amount of\nshells available: ").grid(row=2, column=0)
        self.__shell_option = Spinbox(self.__root, from_=1, to=BOARD_Y * BOARD_Y, textvariable=IntVar(value=50), state="readonly")
        self.__shell_option.grid(row=2, column=1, columnspan=2)
        # endregion

        # region ROW 3
        # Abort / continue buttons
        Button(self.__root, text="Abort game!", bg='gray', command=self.__abort).grid(row=3, column=0)

        Button(self.__root, text="Continue", command=self.__continue_setup).grid(row=3, column=len(MatchType) - 1)

        # Error message variable & label
        self.__error_text = StringVar(value="\n")
        Label(self.__root, textvariable=self.__error_text, fg='red').grid(row=3, column=1, columnspan=len(MatchType) - 2)
        # endregion

        # Configuring resizability
        self.__root.rowconfigure((0, 1, 2, 3), weight=1)

        # Starting up the setup window
        self.__root.mainloop()

    def __continue_setup(self):
        """
        Finishes the setup and moves onto the actual game if the user
        has selected a Match Type.
        """
        # Ensures the user has chosen one of the game types.
        if self.match_type.get() != 0:
            self.shell_amount = IntVar(value=self.__shell_option.get())
            self.continue_setup_bool = True
            self.__abort()
        else:
            self.__error_text.set("You must select\na match type!")

    def __abort(self):
        """
        Destroys the setup window, ending the program.
        """
        self.__root.destroy()


class GameBoard:
    """
    The main window of the program. Creates the abort button, coordinate
    labels, shell counter label and a Board for the enemy.
    """

    def __init__(self, match_type, shell_amount):
        """
        :param match_type: int, value from enum MatchType: how many ships
        there should be in the game.
        """
        self.root = Tk()
        self.root.title("BATTLESHIP 2021 Deluxe Edition")

        # Frame for the coordinate labels
        self.__board_coordinate_frame = Frame(self.root)
        self.__board_coordinate_frame.grid(row=0, column=0)

        # Frame for the Board.
        self.__cpu_frame = Frame(self.__board_coordinate_frame)
        self.__cpu_frame.grid(row=1, rowspan=BOARD_Y, column=1, columnspan=BOARD_Y)

        self.__player_frame = Frame(self.__board_coordinate_frame)
        self.__player_frame.grid(row=1, rowspan=BOARD_Y, column=BOARD_Y + 4, columnspan=BOARD_Y)

        # region Coordinate labels
        # on all sides of the boards.
        for i in range(BOARD_Y):
            # Enemy (CPU) board coordinate frame
            Label(self.__board_coordinate_frame, text=BOARD_X[i]).grid(row=0, column=i + 1)
            Label(self.__board_coordinate_frame, text=BOARD_X[i]).grid(row=BOARD_Y + 1, column=i + 1)

            Label(self.__board_coordinate_frame, text=i).grid(row=i + 1, column=0)
            Label(self.__board_coordinate_frame, text=i).grid(row=i + 1, column=BOARD_Y + 1)
        # endregion

        # The actual board the game is on.
        self.game_board = Board(self.__cpu_frame, match_type, shell_amount)
        self.__shot_counter_label = Label(self.root, textvariable=self.game_board.shot_counter, relief=RAISED, bg='yellow')
        self.__shot_counter_label.grid(row=BOARD_Y + 3, column=0, padx=(0, 300))

        # Abort (quit) button.
        Button(self.root, text="Abort game!", bg='red', command=self.__abort).grid(row=BOARD_Y + 3, column=0)

        self.root.mainloop()

    def __abort(self):
        """
        Destroys the main window, ending the program.
        """
        self.root.destroy()


# endregion


# region Class-independent methods
class MatchType(Enum):
    """
    Enum containing all match types and how many ships each
    of them contains.
    """
    SHORT = 3
    MEDIUM = 4
    LONG = 5


def generate_ship(ships):
    """
    Generates a Ship <new_ship> with new coordinates and a
    proper length corresponding to its type.
    :param ships: ships: list, all ships existing within a board
    :return: Ship <new_ship>, if it could generate a ship with unique
    coordinates; generate_ship if it couldn't create a ship with
    unique coordinates - this simply creates a new ship using the same function.
    """
    ship_coords = []

    # Randomly picks a ship type.
    ship_type = random.choice(list(SHIPS))
    ship_length = SHIPS[ship_type]
    # Orientation: 0 means it's oriented vertically, 1 means horizontally.
    orientation = random.randrange(0, 2)

    # Ship oriented with (vertical) columns, only change the y value.
    if orientation == 0:
        # First coordinate
        ind_x = random.randrange(0, BOARD_Y)
        x = BOARD_X[ind_x]
        y = random.randrange(0, BOARD_Y - ship_length)

        if check_overlap(ships, [x, y]):
            return generate_ship(ships)
        else:
            ship_coords.append(x + str(y))

        for i in range(ship_length - 1):
            y += 1
            if not check_overlap(ships, [x, y]):
                ship_coords.append(x + str(y))
            else:
                return generate_ship(ships)

    # Ship oriented with (horizontal) rows, only change the x value.
    else:
        # First coordinate
        ind_x = random.randrange(0, BOARD_Y - ship_length)
        x = BOARD_X[ind_x]
        y = random.randrange(0, BOARD_Y)

        if check_overlap(ships, [x, y]):
            return generate_ship(ships)
        else:
            ship_coords.append(x + str(y))

        for i in range(1, ship_length):
            x = BOARD_X[ind_x + i]
            if not check_overlap(ships, [x, y]):
                ship_coords.append(x + str(y))
            else:
                return generate_ship(ships)

    # Everything succeeded, return this ship.
    new_ship = Ship(ship_type, ship_coords)
    return new_ship


def check_overlap(ships, coords):
    """
    Checks whether or not these coordinates <coords> already exist with another ship.
    :param ships: ships: list, all ships existing within a board
    :param coords: list, x and y value of the wanted coordinate.
    :return: True, if there is even one ship with this coordinate <coord>;
    False, if this coordinate <coord> is not contained in any ship's coordinates.
    """
    coord = coords[0] + str(coords[1])
    if in_ship_coordinates(ships, coord) is not None:
        return True
    return False


def in_ship_coordinates(ships, coord):
    """
    Searches through every Ship in <ships> and checks if the coordinaate
    <coord> is in any of them. Returns the first ship with this coordinate.
    :param ships: list, all ships existing within a board
    :param coord: string, the coordinate searched for
    :return: Ship <s>, if <coord> is contained in its coordinates;
    None, if <coord> is not in any ships coordinates.
    """
    for s in ships:
        if coord in s.coordinates:
            return s
    return


def errorpopup(master, title, msg):
    """
    Hides the <master> window and shows a popup window with <title> and <msg> in it.
    When the user closes this popup, the program quits using sys.exit().
    :param master: tkinter window, main window to be hid when an error pops up
    :param title: string, error popup title
    :param msg: string, error description
    """
    master.master.withdraw()
    messagebox.showerror(title, msg)
    exit()


# endregion


def main():
    rule_setup = RuleSetupGUI()

    # If the player decides to abort the game at the rule setup, exit
    if not rule_setup.continue_setup_bool:
        return

    GameBoard(rule_setup.match_type.get(), rule_setup.shell_amount.get())


if __name__ == "__main__":
    main()
