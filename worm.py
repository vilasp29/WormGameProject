#!/usr/bin/env python3
# -*- coding: utf-8 -*- 
import os
import re
import random
import sys
import time
import curses
from curses import wrapper
import pdb
#from getbestscore import getbestscore
#import getbestscore

"""
" Constants
"""

MAX_SLEEP = 600
MIN_SLEEP = 50
SLEEP_INCR = 10
VERT_SLEEP_MULT = 1.4 # slow down vertical sleep
SPEED_LIMIT = 1000 # Sleep is subtracted from this to show as speed
INIT_SEG = 10
OFFSET = 2 #offset from max x and y so that worm does not eat the border

class Direction :
	DIR_UP = 1
	DIR_DOWN = 2
	DIR_RIGHT = 8
	DIR_VERT = DIR_UP | DIR_DOWN
	DIR_LEFT = 4
	DIR_RIGHT = 8
	DIR_HORIZ = DIR_LEFT | DIR_RIGHT

	def __init__(self,wh) :
		self.where = wh

	def __eq__(self, oth) :
		if oth == None :
			return False
		elif self.where == oth.where :
			return True
		else : 
			return False

	def opposite(self) :
		retval = self.where ^ Direction.DIR_HORIZ if self.where & Direction.DIR_HORIZ else self.where ^ Direction.DIR_VERT 
		return Direction(retval)


	def isLeft(self) :
		#debugprint(str(bool(self.where & Direction.DIR_LEFT))+" "+ self.where)
		return bool(self.where & Direction.DIR_LEFT)

	def isRight(self) :
		#debugprint(str(bool(self.where & Direction.DIR_RIGHT))+" "+ self.where)
		return bool(self.where & Direction.DIR_RIGHT)

	def isUp(self) :
		#debugprint(str(bool(self.where & Direction.DIR_UP))+" "+ self.where)
		return bool(self.where & Direction.DIR_UP)

	def isDown(self) :
		#debugprint(str(bool(self.where & Direction.DIR_DOWN))+" "+ self.where)
		return bool(self.where & Direction.DIR_DOWN)

	def isHoriz(self) :
		return bool(self.where & Direction.DIR_HORIZ)
		#return self.isRight() or self.isLeft()

	def isVert(self) :
		return bool(self.where & Direction.DIR_VERT)
		#return self.isDown() or self.isUp()

	def setWhere(wh) :
		self.where(wh)

	def setDirection(self,dir):
		self.dir = dir

class Location :
	maxX = -1
	maxY = -1

	def __init__(self,y,x,whence="", lc = None) :
		assert( Location.maxX > 0 )
		assert( Location.maxY > 0 )
		if whence == "Random" :
			self.y , self.x = random.randint(1,Location.maxY), random.randint(1,Location.maxX)
		elif lc != None :
			self.y , self.x = lc.y, lc.x
		else :
			self.y ,self.x  = y,  x
			

	def __eq__(self, oth) :
		if oth == None :
			return False
		if self.y == oth.y and self.x == oth.x :
			return True
		else : 	
			return False

	def __ne__(self, oth) :
		if oth != None :
			return not ( self == oth )
		else :
			return True

	def __sub__(self, oth) :
		if oth != None :
			return self.y - oth.y, self.x - oth.x
		else :
			raise ValueError("Location to be subtracted is None")

	def drawRay(self, oth, win) :
		if oth == None :
			return
		curses.echo()
		xdif = self.x - oth.x	
		ydif = self.y - oth.y	
		if xdif < 0 :
			xdif = xdif * -1
			hstarty , hstartx = self.y , self.x
		else :
			hstarty , hstartx = oth.y , oth.x
		if xdif > 2 :
			win.hline(hstarty, hstartx+1 , "-", xdif-1)

		if ydif < 0 :
			ydif = ydif * -1
			vstartx , vstarty = self.x , self.y
		else :
			vstartx , vstarty = oth.x , oth.y
		if ydif > 2 :
			win.vline(vstarty+1, vstartx , "|", ydif-1)

		win.nodelay(0)
		win.getch()			
		if xdif > 2 :
			win.hline(hstarty, hstartx+1 , " ", xdif-1)
		if ydif > 2 :
			win.vline(vstarty+1, vstartx , " ", ydif-1)
		win.nodelay(1)

		curses.noecho()


	def getAdjacent(self, l_dir) :
		lc = Location(0,0,"",self)
		retDir = l_dir
		if l_dir.where & Direction.DIR_UP :
			if (lc.moveUp() == "CANT_UP") :
				if (lc.moveRight() == "CANT_RIGHT") :
					lc.moveLeft() 
					retDir = Direction(Direction.DIR_LEFT)
				else :
					retDir = Direction(Direction.DIR_RIGHT)

		elif l_dir.where & Direction.DIR_DOWN :
			if (lc.moveDown() == "CANT_DOWN") :
				if (lc.moveLeft() == "CANT_LEFT") :
					lc.moveRight() 
					retDir = Direction(Direction.DIR_RIGHT)
				else :
					retDir = Direction(Direction.DIR_LEFT)

		elif l_dir.where & Direction.DIR_LEFT :
			if (lc.moveLeft() == "CANT_LEFT") :
				if (lc.moveUp() == "CANT_UP") :
					lc.moveDown() 
					retDir = Direction(Direction.DIR_DOWN)
				else :
					retDir = Direction(Direction.DIR_UP)
		else :
			if (lc.moveRight() == "CANT_RIGHT") :
				if (lc.moveDown() == "CANT_DOWN") :
					lc.moveUp() 
					retDir = Direction(Direction.DIR_UP)
				else :
					retDir = Direction(Direction.DIR_DOWN)
		assert(lc != self)
		return lc, retDir

	def isAdjacent(self, oth, l_Dir) :
		if oth == None :
			return False

		dify, difx  = self - oth # Diff between two locations
		#debugprint("Diff(x,y) : " + str(difx) + " " + str(dify))

		if  ( difx == -1  and dify == 0 and  l_Dir.isRight() == True):
			return True
		elif  ( difx == 1  and dify == 0 and  l_Dir.isLeft() == True):
			return True
		elif  ( dify == -1  and difx == 0 and  l_Dir.isDown() == True):
			return True
		elif  ( dify == 1  and difx == 0 and  l_Dir.isUp() == True):
			return True
		else :	
			return False

	def curLocation() :
		return y, x

	def moveUp(self) :
		if (self.y <= 1 ) :
			return "CANT_UP" 
		else :
			self.y = self.y - 1
			return "DONE"
			
	def moveDown(self) :
		if (self.y >= Location.maxY ) :
			return "CANT_DOWN"
		else :	
			self.y = self.y + 1
			return "DONE"
		
	def moveLeft(self) :
		if (self.x <= 1 ) :
			return "CANT_LEFT"
		else :
			self.x = self.x - 1
			return "DONE"

	def moveRight(self) :
		if (self.x >= Location.maxX ) :
			return "CANT_RIGHT"
		else :	
			self.x = self.x + 1
			return "DONE"

	def setmax(co_ord) :
		global VERT_SLEEP_MULT
		Location.maxY = co_ord[0] - OFFSET
		Location.maxX = co_ord[1] - OFFSET
		VERT_SLEEP_MULT = int((Location.maxX/Location.maxY) * 0.5)

	def printChar(self,win, ch, atr = None) :
		curses.echo()
		win.addch(self.y,self.x,ch,atr) if atr != None else  win.addch(self.y,self.x,ch)
		curses.noecho()

class Locatable :
	def __init__(self,loc):
		self.loc = loc

	def getLocation(self):
		return self.loc

	def setLocation(self,loc):
		self.loc = loc

	def __eq__(self, oth) :
		if oth == None :
			retval = False 
		elif self.loc == oth.loc :
			retval =  True 
		else  :
			retval =  False 
		return retval

	def printChar(self, win, ch, atr = None) :
		self.loc.printChar(win,ch,atr)


class Segment(Locatable) :
	disp_char = "o"
	disp_1_char = "@"
	erase_char = " "

	def __init__(self,loc):
		Locatable.__init__(self,loc)

	def erase(self,win) :
		self.printChar(win, Segment.erase_char)

	def show(self,win,first=False) :
		if first :
			self.printChar(win, Segment.disp_1_char)
		else :
			self.printChar(win, Segment.disp_char)
		
	def getSegatNextLoc(self, l_dir) :
		lc, retDir = self.loc.getAdjacent(l_dir)
		return Segment(lc), retDir

class Arena :
	def __init__(self,stdscr) :
		self.rows, self.cols = stdscr.getmaxyx()
		self.rows = self.rows - 1
		self.cols = self.cols - 1
		self.worm = None
		self.win =  stdscr
		self.addFood(Food(Location(0,0,"Random")))

	def getWorm(self) :
		return self.worm

	def getWormDir(self) :
		return self.worm.getDir()

	def setNodelay(self, val) :
		val = 1 if val > 0 else 0
		self.win.nodelay(val) 

	def addFood(self,fd):
		self.food = fd		
		self.foodEaten = False

	def removeEatenFood(self,fd):
		fd.erase(self.win)
		self.food = None
		self.foodEaten = False

	def getFoodLocation(self) :
		return self.food.getLocation() if self.food != None else None

	def setWorm(self, w) :
		self.worm = w
			
	def getWormHeadLoc(self) :
		return self.worm.getHeadLoc() if self.worm != None else None

	def isWormAlive(self) :
		return self.worm.alive if self.worm != None else None

	def getWormSleep(self) :
		return self.worm.getSleep()  if self.worm != None else None

	def speedUpWorm(self):
		self.worm.speedUp()

	def speedDownWorm(self):
		self.worm.speedDown()

	def eraseWorm(self,win) :
		self.worm.erase(win)

	def moveWorm(self,dr) :	
		self.worm.move(dr)

	def getWin(self) :
		return self.win

	def getScore(self) :
		return len (self.worm.segs) - (INIT_SEG) if self.worm != None else 0 
			

	def show(self,init=False) :
		if init == True :
			curses.echo()
			self.win.border()
			self.win.addstr(self.rows,1,"Press F12 to exit",curses.A_BOLD)
			curses.noecho()
		else  :
			#b_scr = " BEST SCORE : " + str(getBestScore()) + " "
			b_scr = ""
			scr = " SCORE : " + str(self.getScore()) + " "
			spd = " SPEED : " + str(self.worm.getSpeed()) + " "
			cc = len(b_scr+scr+spd)
			self.win.addstr(self.rows,self.cols - cc ,b_scr+scr+spd,curses.A_BOLD)

		if self.food != None :	
			self.food.show(self.win)
		if self.worm != None :
			self.worm.show(self.win)

		self.win.refresh()

	def acceptInput(self) :
		key = self.win.getch()
		dr = None
		if key == curses.KEY_UP :
			dr = Direction(Direction.DIR_UP)
		elif key == curses.KEY_DOWN :
			dr = Direction(Direction.DIR_DOWN)
		elif key == curses.KEY_LEFT :
			dr = Direction(Direction.DIR_LEFT)
		elif key == curses.KEY_RIGHT :
			dr = Direction(Direction.DIR_RIGHT)
		return dr, key

class Worm :
	def __init__(self,dir,loc, arena, numSeg = 1) :
		self.arena = arena
		self.size = 1
		self.segs = []
		l_seg = Segment(loc)
		self.segs.append(l_seg)
		l_dir = dir
		while numSeg > 1 :
			numSeg = numSeg - 1
			l_seg, l_dir = l_seg.getSegatNextLoc(l_dir)
			self.segs.insert(0,l_seg)
			self.size = self.size + 1
		self.sleep = MAX_SLEEP
		self.alive = True
		self.dir = l_dir

	def getDir(self) :
		return self.dir

	def setDir(self, l_dir) :
		self.dir = l_dir

	def getSleep(self) :
		return  int(self.sleep * VERT_SLEEP_MULT) if self.dir.isVert() else self.sleep

	def getSpeed(self) :
		return SPEED_LIMIT - self.sleep

	def getHeadLoc(self) :
		return self.segs[0].getLocation()

	def speedUp(self) :
		self.sleep = MIN_SLEEP if (self.sleep < MIN_SLEEP) else  (self.sleep - SLEEP_INCR)

	def speedDown(self) :
		self.sleep = MAX_SLEEP if self.sleep > MAX_SLEEP else self.sleep + SLEEP_INCR

	def erase(self,win) :
		for s in self.segs  :
			s.erase(win) 

	def show(self,win) :
		self.segs[0].show(win,True)
		for s in self.segs[1:] :
			s.show(win)

	def move(self,newDir) :

		if self.dir.opposite() == newDir : # if worm tries to move opposite to curr dir then it is eating itself
			self.alive = False # and hence dead
			return

		if self.segs[0].loc.isAdjacent(self.arena.getFoodLocation(),newDir) : #is head of worm adjacent to food in direction of travel?
			self.segs.insert(0,Segment(self.arena.getFoodLocation()))     #eat the food by adding a seg ahead of head where food was
			self.arena.removeEatenFood(self.arena.food) 		      # Remove food from arena
			self.size = self.size + 1				      # increase size of the worm
			self.arena.addFood(Food(Location(0,0,"Random")))	      # Add new food at a random location
			self.speedUp()						      # increase speed of the worm
			self.setDir(newDir)					      # set the direction of the worm to current direction of travel given by the arrow key
		else : # No food eaten move first segment, delet last segment
			l_seg, l_dir = self.segs[0].getSegatNextLoc(newDir)  	      #create a seg ahead of head
			self.segs.insert(0,l_seg) 				      #add a seg ahead of head
			del self.segs[-1] 					      # delete last seg
			self.setDir(l_dir)

		if self.segs[0] in self.segs[1:] : 				      # check if worm has eaten itself
			self.alive = False         			  	      # set worm as dead
			
		return	

class Food(Locatable) :
	disp_char = "X"
	erase_char = " "

	def __init__(self,loc) :
		Locatable.__init__(self, loc)
	
	def show(self,win) :
		self.printChar(win, Food.disp_char,curses.A_BOLD)

	def erase(self,win) :
		self.printChar(win, Food.erase_char)

class GameController :
	def __init__(self,arena,lvl) :
		self.level = lvl
		self.arena = arena
		curses.curs_set(0) #Cursor invisible
		curses.cbreak()
		self.arena.setNodelay(1)

	def doHelp(self) :
		win2 = curses.newwin(20,60,1,150)
		win2.border()
		win2.addstr(1,1,"Help",curses.A_BOLD)
		win2.addstr(4,1,"Keys:")
		win2.addstr(5,1,"	F1  	    = Help")
		win2.addstr(6,1,"	F4  	    = Ray gun (for Beginner only)")
		win2.addstr(7,1,"	F9  	    = Slower (for non Advanced only)")
		win2.addstr(8,1,"	F11  	    = Faster")
		win2.addstr(9,1,"	F12 	    = Quit")
		win2.addstr(10,1,"	Arrow Keys  = Move the worm")
		win2.getch()
		win2.erase()
		win2.refresh()
		del win2

	def gameOver(self) :
		win2 = curses.newwin(7,45,15,80)
		win2.border()
		win2.addstr(3,18,"GAME OVER",curses.A_BOLD + curses.A_REVERSE  + curses.A_BLINK)
		win2.getch()
		win2.erase()
		win2.refresh()
		del win2
		
	def doRayGun(self) :
		if self.level == "BEGINNER":
			self.arena.getWormHeadLoc().drawRay(self.arena.getFoodLocation(),self.arena.getWin())
		
	def run(self) :
		self.arena.show(True) #Initial show of Arena
		if self.arena.getWorm() == None :
			self.arena.setWorm(Worm(Direction(Direction.DIR_RIGHT),Location(1,1),self.arena,INIT_SEG))

		self.arena.show() #show of Arena after worm is added
		while self.arena.isWormAlive() :
			dr, key  = self.arena.acceptInput()

			if key == curses.KEY_F1 :
				self.doHelp()
			elif key == curses.KEY_F4 :
				self.doRayGun()
			elif key == curses.KEY_F9 : # Slower
				if self.level != "ADVANCED" :
					self.arena.speedDownWorm()
			elif key == curses.KEY_F11 : # Faster
				self.arena.speedUpWorm()
			elif key == curses.KEY_F12 :
				break

			self.arena.eraseWorm(self.arena.win)

			if dr == None :
				dr = self.arena.getWormDir()
				#dr = self.arena.worm.dir

			self.arena.moveWorm(dr)
			self.arena.show() 				#show of Arena
			curses.napms(self.arena.getWormSleep())

		self.gameOver()

def debugprint(str) :
	y, x = DEBUG_WIN.getmaxyx()
	DEBUG_WIN.addstr(y-1,40, "                        ")
	DEBUG_WIN.addstr(y-1,40, str)

def main(stdscr) :
	global DEBUG_WIN 
	DEBUG_WIN = stdscr

	try :
		lvl =  os.environ['WORM_LEVEL']
	except :
		lvl = "BEGINNER"

	Location.setmax(stdscr.getmaxyx())

	a = Arena(stdscr)
	
	g = GameController(a,lvl)

	g.run()

##
# default main
##
#print(dir("getbestscore"))
#l = input("Key")
wrapper(main)
curses.nocbreak()
curses.echo()
curses.curs_set(1) #Cursor normal
curses.endwin()
exit(0)
