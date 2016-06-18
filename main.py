'''
	For license, see: LICENSE
'''

import http.client, sys, json, os, vk, datetime, time, imghdr, shutil, collections, urllib
import requests as r
from PIL import Image
from redditdownload import download as DL

class Utils:

	@staticmethod
	def addTime(timestamp, mins):
		return time.mktime((datetime.datetime.fromtimestamp(float(timestamp)) + 
							datetime.timedelta(minutes=mins)).timetuple())

	@staticmethod
	def isImageTooBig(filepath):
		im = Image.open(filepath)
		filex,filey = im.size
		im.close()
		return (filey/filex) > 3

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

	def fileUpload(self, group_id, file_name, file_path, too_big):
		n, ext = os.path.splitext(file_name)
		upload_data = {}

		try:
			if ext == ".gif" or too_big:
				upload_data = self.vkapi.docs.getWallUploadServer(group_id=group_id)
			else:
				upload_data = self.vkapi.photos.getWallUploadServer(group_id=group_id)
		except vk.api.VkAPIError as e:
			print ("ERROR: Couldn't get the upload server:", e)
			return {}
		except:
			print ("ERROR: Couldn't get the upload server:", sys.exc_info()[0])
			return {}

		data = {}
		files = {'photo': (file_name, open(file_path, 'rb'))}
		url = upload_data['upload_url'].split('?')[0]

		for key, value in urllib.parse.parse_qs(upload_data['upload_url'].split('?')[1]).items():
			data[key] = value

		upload_response = r.post(url, data, files=files)
		upload_response = upload_response.json()

		if "__error" in upload_response:
			print ("ERROR: Couldn't upload the file: ", upload_response["__error"])
			return {}

		return upload_response

	def fileSave(self, group_id, file_name, file_path, too_big, upload_response, group_name):
		n, ext = os.path.splitext(file_name)

		try:
			if ext == ".gif" or too_big:
				save_response = self.vkapi.docs.save(file=upload_response["file"], 
												title="re/" + group_name + "/" + n)
			else:
				save_response = self.vkapi.photos.saveWallPhoto( group_id=group_id, 
															server=upload_response["server"], 
															hash=upload_response["hash"], 
															photo=upload_response["photo"])
			save_response = save_response[0]
		except vk.api.VkAPIError as e:
			print ("ERROR: Couldn't save file on the server:", e)
			return {}
		except:
			print ("ERROR: Couldn't save file on the server:", sys.exc_info()[0])
			return {}

		return save_response

	def filePost(self, group_id, file_name, file_path, too_big, save_response, group_name, publish_time):
		n, ext = os.path.splitext(file_name)
		source = "https://reddit.com/r/" + group_name + "/comments/" + n + "/"

		try:
			if ext == ".gif" or too_big:
				post_id = self.vkapi.wall.post(owner_id=group_id, 
											from_group=1, 
											attachments=str(save_response["id"]) + "," + source, 
											publish_date=publish_time)
			else:
				post_id = self.vkapi.wall.post(owner_id=group_id, 
											from_group=1, 
											attachments = str(save_response["id"]) + "," + source,
											publish_date=publish_time)

		except vk.api.VkAPIError as e:
			print ("ERROR: Couldn't post the file: ", e)
			return {}

		return post_id


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
		self.download_dir = "pics"
		self.pics_dir = self.download_dir + "/" + self.name
		self.scheduled_posts = []
		self.post_time = time.time() # now
		self.gaps = []


	def download(self):
		if not os.path.exists(self.download_dir):
			os.mkdir(self.download_dir)

		shutil.rmtree(self.pics_dir, ignore_errors=True)

		args = lambda: None
		args.reddit = self.name
		args.dir = self.pics_dir
		args.last = ''
		args.score = 0
		args.num = 25
		args.update = False
		args.sfw = False
		args.nsfw = False
		args.regex = None
		args.verbose = False

		print ("    Downloading...")
		DL(args)

		path, dirs, files = next(os.walk(args.dir))

		print ("    Downloaded:", len(files))
		return len(files)
		
	def findTimeGaps(self, posts, max_gap):
		if len(posts) <= 0 or posts[0] == 0:
			return 0

		self.post_time = posts[-1:][0]['date']
		previous_time = posts[1]['date']

		for p in posts[1:]:
			if (p['date'] - previous_time) > max_gap:
				self.gaps.append(previous_time + max_gap)
			previous_time = p['date']

		return len(self.gaps)

	def getTime(self):
		if len(self.gaps) > 0:
			return self.gaps.pop()

		self.post_time = Utils.addTime(self.post_time, 60)
		return self.post_time if self.post_time > time.time() else time.time()
		

	def getScheduledPosts(self):
		self.scheduled_posts = self.conn.vkapi.wall.get(owner_id=self.id, 
														count=100, 
														filter="postponed")
		return self.scheduled_posts[0]

	def loadHistory(self):
		mode = 'r' if os.path.exists(self.history_file) else 'a'

		with open(self.history_file, mode) as data_file:
			try:
				data = json.load(data_file)
				self.history = data['files']
			except ValueError:
				print ("WARNING: Empty file or broken json structure")

		self.history = collections.deque(self.history)

		return len(self.history)

	def addToHistory(self, str):
		if len(self.history) >= 200:
			self.history.popleft()

		self.history.append(str)

	def inHistory(self, str):
		if len(self.history) <= 0:
			return False

		for item in self.history:
			if item == str:
				return True

		return False

	def saveHistory(self):
		with open(self.history_file, "w") as data_file:
			try:
				data_file.write(json.dumps({"files" : list(self.history)}))
			except ValueError:
				print ("WARNING: Could not save history")

	def post(self):
		print ("")
		print ("GROUP:", self.name)

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
			print ("    History: ", len(self.history))

		if self.getScheduledPosts() <= 0:
			print ("WARNING: No scheduled posts")
		else:
			print ("    Scheduled posts: ", self.scheduled_posts[0])

		if self.findTimeGaps(self.scheduled_posts, 3600) > 0:
			print ("INFO: Gaps found")


		posted = 0

		for file_name in os.listdir(self.pics_dir):
			if self.inHistory(file_name):
				continue

			print("    Posting", file_name)

			file_path = self.pics_dir + "/" + file_name
			too_big = Utils.isImageTooBig(file_path)
			upload_response = {}
			save_response = {}
			post_id = {}

			# TODO: refactor this

			retry = 0
			while retry < 5 and not upload_response:
				upload_response = self.conn.fileUpload(abs(self.id), file_name, file_path, too_big)
				retry += 1
				time.sleep(1)

			if retry >= 5 and not upload_response:
				print("ERROR: Failed to get upload_response")
				continue

			retry = 0
			while retry < 5 and not save_response:
				save_response = self.conn.fileSave(abs(self.id), file_name, file_path, too_big, upload_response, self.name)
				retry += 1
				time.sleep(1)

			if retry >= 5 and not save_response:
				print("ERROR: Failed to get save_response")
				continue

			retry = 0
			while retry < 5 and not post_id:
				post_id = self.conn.filePost(self.id, file_name, file_path, too_big, save_response, self.name, self.getTime())
				retry += 1
				time.sleep(1)

			if retry >= 5 and not post_id:
				print("ERROR: Failed to get post_id")
				continue


			posted += 1
			self.addToHistory(file_name)
			time.sleep(1)
			
		print("    Files posted:", posted)
		print("    Files scheduled:", self.scheduled_posts[0] + posted)

		self.saveHistory()
		
		

if __name__ == "__main__":
	conn = Connection()

	g_meirl = Group(conn, 'me_irl', -99583108)
	g_4chan = Group(conn, '4chan', -99632260)
	g_bpt	= Group(conn, 'BlackPeopleTwitter', -99632081)

	g_meirl.post()
	g_4chan.post()
	g_bpt.post()