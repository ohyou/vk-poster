import http.client, sys, json, os, vk, datetime, time, imghdr
import requests as r
from PIL import Image

class Connection:
	def __init__(self):
		self.established = False
		self.attempts = 0
		self.vkapi = None

	# API requests here

	def authorize(self):
		session = vk.Session(access_token="2ab05ccf3630161b846412658e9d1bd40de756592513a6c0f3aab5a63f59655029c1190583165c1e22f9f")
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
		#self.downloaded = False

	# Downloading with os.system("downloader.py")
	# Posting logic here
	# Utils here or in a separate class?

	# TODO: posting time management

	# def download
	# 	return len(arr)

	# def getTime #	find a hole or +1h from last post
	#	return string?

	# def addTime # utils?
	#	return string?

	def getScheduledPosts(self):
		self.scheduled_posts = self.conn.vkapi.wall.get(owner_id=self.id, count=100, filter="postponed")
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
			pass

		if self.conn.authorize() == False:
			print ("ERROR: API authorization failed, aboring")
			pass

		if self.loadHistory() <= 0:
			print ("WARNING: No history found")
		else:
			print ("	History: ", len(self.history))

		if self.getScheduledPosts() <= 0:
			print ("WARNING: No scheduled posts")
		else:
			print ("	Scheduled posts: ", self.scheduled_posts[0])

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