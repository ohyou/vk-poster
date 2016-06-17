'''
	For license, see: LICENSE
'''

import http.client, sys, json, os, vk, datetime, time, imghdr
import requests as r
from PIL import Image
from redditdownload import download as DL

class Utils:

	@staticmethod
	def addTime(timestamp, mins):
		return time.mktime((datetime.datetime.fromtimestamp(float(timestamp)) + 
							datetime.timedelta(minutes=mins)).timetuple())

class Connection:
	def __init__(self):
		self.established = False
		self.attempts = 0
		self.vkapi = None

	# API requests here

	def authorize(self):
		if os.path.exists("access_token"):
			file = open("access_token")
			session = vk.Session(access_token=file.read())
			self.vkapi = vk.API(session)
		return self.vkapi != None

	# def request
	#	return bool

	# def get # wall/scheduled data
	#	return json?

	def establish(self):
		conn = http.client.HTTPConnection('www.google.com')
		try:
			conn.request("HEAD", "/")
			self.established =  True
		except:
			print("Connection error:", sys.exc_info()[0])
			self.established =  False
		return self.established

class Group:
	def __init__ (self, connection, name, id):
		self.conn = connection
		self.name = name
		self.id = id
		self.history = []
		self.history_file = self.name + ".json"
		self.scheduled_posts = []
		self.post_time = time.time() # now
		self.gaps = []


	def download(self):
		args = lambda: None
		args.reddit = self.name
		args.dir = "pics/" + self.name
		args.last = ''
		args.score = 0
		args.num = 30
		args.update = False
		args.sfw = False
		args.nsfw = False
		args.regex = None
		args.verbose = False

		DL(args)

		path, dirs, files = next(os.walk(args.dir))
		return len(files)
		
	def findTimeGaps(posts, max_gap):
		if len(posts) <= 0:
			return []

		self.post_time = posts[-1:]['date']
		previous_time = posts[1]['date']

		for p in posts[1:]:
			if (p['date'] - previous_time) > max_gap:
				self.gaps.append(previous_time + max_gap)
			previous_time = p['date']

		return len(self.gaps)

	def getTime(self):
		if len(self.gaps) > 0:
			return self.gaps.pop()

		return Utils.addTime(self.post_time, 60)
		

	def getScheduledPosts(self):
		self.scheduled_posts = self.conn.vkapi.wall.get(owner_id=self.id, 
														count=100, 
														filter="postponed")
		return self.scheduled_posts[0]

	def loadHistory(self):
		mode = 'a' if os.path.exists(self.history_file) else 'w'

		with open(self.history_file, mode) as data_file:
			try:
				data = json.load(data_file)
				self.history = data['files']
			except ValueError:
				print ("WARNING: Empty file or broken json structure")

		return len(self.history)

	def post(self):
		if self.conn.establish() == False:
			print ("ERROR: No connection, aborting")
			return

		if self.conn.authorize() == False:
			print ("ERROR: API authorization failed, aborting")
			return

		if self.download() <= 0:
			print ("ERROR: Nothing was downloaded")
			return

		if self.loadHistory() <= 0:
			print ("WARNING: No history found")
		else:
			print ("	History: ", len(self.history))

		if self.getScheduledPosts() <= 0:
			print ("WARNING: No scheduled posts")
		else:
			print ("	Scheduled posts: ", self.scheduled_posts[0])

		if self.findTimeGaps() > 0:
			print ("INFO: Gaps found")

		self.post_time = self.getTime()

		# Loop through files omitting ones in self.history and post them
		# Posting with self.conn
		
		print ("	posting to", self.name)

if __name__ == "__main__":
	conn = Connection()

	g_meirl = Group(conn, 'me_irl', -99583108)
	g_4chan = Group(conn, '4chan', -99632260)
	g_bpt	= Group(conn, 'BlackPeopleTwitter', -99632081)

	g_meirl.post()
	g_4chan.post()
	g_bpt.post()