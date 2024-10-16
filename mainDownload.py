import os
import requests
from bs4 import BeautifulSoup
import time
import re
import random
from PIL import Image
import io
from urllib.parse import urljoin
from bs4.element import Tag

class Downloading:
	def __init__(self, web_name):
		self.user_agents = [
			'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36',
			'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36',
			'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/97.0',
			'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/98.0.1108.43',
			'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Safari/537.36',
		]
		self.web_names = ["blacked.booru.org", "rule34.xxx", "gelbooru.com", "xbooru.com", "yande.re"]
		self.simple_name = ["blacked", "rule34", "gelbooru", "xbooru", "yande"]
		self.page_size = {"blacked.booru.org": 20, "rule34.xxx": 42, "gelbooru.com": 42, "xbooru.com": 42,
						  "yande.re": 40,
						  "blacked": 20, "rule34": 42, "gelbooru": 42, "xbooru": 42, "yande": 40}

		self.tags = self.get_tags()

		if web_name in self.web_names:
			self.name = self.web_names[self.web_names.index(web_name)]
			self.save_name = self.simple_name[self.web_names.index(web_name)]
		elif web_name in self.simple_name:
			self.name = self.web_names[self.simple_name.index(web_name)]
			self.save_name = self.simple_name[self.simple_name.index(web_name)]
		else:
			assert "Have not your web_name"


		self.pid_start, self.pid_end = self.get_page()

		self.url = self.get_url(self.pid_start)

		self.conter_pid = 0

		self.save_folder = "./images"

	def chance_web_name(self):
		web_name = input("Input new web_name: ")
		if web_name in self.web_names:
			self.name = self.web_names[self.web_names.index(web_name)]
		elif web_name in self.simple_name:
			self.name = self.web_names[self.simple_name.index(web_name)]
		else:
			print("places input right name!")
			self.chance_web_name()

	def chance_tags(self):
		print("Enter Tags: ", end='')
		self.tags = input().split()
		print(f'searching tags: {self.tags}')

	def get_tags(self):
		print("Enter Tags: ", end='')
		tags = input().split()
		print(f'searching tags: {tags}')
		return tags

	def chance_page(self):
		self.pid_start, self.pid_end = self.get_page()
		self.url = self.get_url(self.pid_start)

	def get_page(self):
		pages = input("Enter you want to download page: ")
		pages = list(map(int, pages.split(" ")))
		start, end = 0, 0
		if len(pages) == 2 and isinstance(pages[0], int) and isinstance(pages[1], int):
			start, end = pages
		elif isinstance(pages[0], int):
			start = pages[0]
		else:
			return self.get_page()

		if start < 1:
			start = 1
		if end < 2:
			end = 1
		if start >= end:
			end = start

		pid_start = (start - 1) * self.page_size[self.name]
		if end:
			pid_end = end * self.page_size[self.name]
			return pid_start, pid_end
		return pid_start, float('inf')

	def headers(self):
		return {'User-Agent': random.choice(self.user_agents)}

	def contentpresent(self, url):
		content = 0
		try:
			res = requests.get(url, headers=self.headers())
			res.raise_for_status()  # 检查 HTTP 响应状态码
			sf = BeautifulSoup(res.text, 'html.parser')
			if self.name in ["blacked.booru.org", "rule34.xxx", "xbooru.com"]:
				content = sf.findAll('span', {'class': 'thumb'})
			elif self.name in ["gelbooru.com"]:
				content = sf.findAll('article', {'class': 'thumbnail-preview'})
			elif self.name in ["yande.re"]:
				content = sf.findAll('a', {'class': "thumb"})
			print(url)
			if len(content) != 0:
				return True
		except requests.exceptions.RequestException as e:
			print(url)
			print(f"An error occurred: {e}")
		return False

	def res_get(self, url):
		max_attempts = 5
		attempt_count = 0
		success = False
		res = 0
		while attempt_count < max_attempts and not success:
			try:
				res = requests.get(url, headers=self.headers()).text
				success = True
			except Exception as e:
				time.sleep(5)
				attempt_count += 1
				print(f"Error occurred: {e} \nRetrying... (attempt {attempt_count}/{max_attempts})")
		else:
			if not success:
				return 0
		return res

	def image_ext(self, url):
		url = re.split('\.jpg|\.png|\.jpeg|\.gif', url)[0]
		try:
			res_png, into = self.down_img(f"{url}.png", mod="img")
			if res_png:
				return f"{url}.png", into

			res_jpeg, into = self.down_img(f"{url}.jpeg", mod="img")
			if res_jpeg:
				return f"{url}.jpeg", into

			res_jpg, into = self.down_img(f"{url}.jpg", mod="img")
			if res_jpg:
				return f"{url}.jpg", into

			res_gif, into = self.down_img(f"{url}.gif", mod="img")
			if res_gif:
				return f"{url}.gif", into
		except Exception as e:
			print("image_ext error: ", e)

	def get_http_error(self, res):  # 加入新的判断语句用于去除404界面
		if b'404 Not Found' in res:
			return True
		if b"https://gelbooru.com/layout/404.jpg" in res:
			return True
		if b'class="error-code"' in res:
			return True
		return False

	def webname_findAll(self, soup):  # 找到页面对应的原图网址
		content = 0
		if self.name in ["blacked.booru.org", "rule34.xxx", "xbooru.com"]:
			content = soup.findAll('span', {'class': 'thumb'})
		elif self.name in ["gelbooru.com"]:
			content = soup.findAll('article', {'class': 'thumbnail-preview'})
		elif self.name in ["yande.re"]:
			content = soup.findAll('a', {'class': "directlink largeimg"})
		return content

	def get_url(self, pid_start):
		if self.name in ["blacked.booru.org", "rule34.xxx", "gelbooru.com", "xbooru.com"]:
			return f"https://{self.name}/index.php?page=post&s=list&tags={'+'.join(self.tags)}+&pid={pid_start}"
		elif self.name in ["yande.re"]:
			page = pid_start // self.page_size[self.name] + 1
			return f"https://{self.name}/post?page={page}&tags={'+'.join(self.tags)}"

	def get_img_url(self, soup):  # 找到原图页面的高清原图片网址用于下载图片
		if self.name in ["blacked.booru.org", "rule34.xxx", "xbooru.com", "gelbooru.com"]:
			url = soup.find('img', {'id': 'image'})['src']
			if ('//samples/' in url):
				img_url = url.replace('samples', 'images')
				img_url = img_url.replace('sample_', '')
				img_url = img_url.split('?')[0]
			else:
				img_url = url.split('?')[0]
			return img_url
		elif self.name in ["yande.re"]:
			url = soup.find('a', {'class': 'original-file-changed'})['href']
			return url

	def download_link(self, url_soup, down_url):
		if self.name in ["yande.re"]:
			link = url_soup['href']
			try:
				_, into = self.down_img(link)
			except Exception:
				into = False
			return link, into
		elif self.name in ["blacked.booru.org", "rule34.xxx", "xbooru.com", "gelbooru.com"]:
			link = urljoin(down_url, url_soup.a['href'])
			main = self.res_get(link)
			if not main:
				return link, False
			soupf = BeautifulSoup(main, 'lxml')
			img_url = link
			try:
				img_url, into = self.image_ext(self.get_img_url(soupf))
			except Exception:
				into = False
		return img_url, into


	def down_img(self, url, mod="img"):
		into = False
		count = 0
		while count < 5:
			try:
				res = requests.get(url, headers=self.headers()).content
				if self.get_http_error(res):
					return False, into
				image = Image.open(io.BytesIO(res))
				image.verify()
				into = self.down_save(url, res)
				return True, into
			except Exception as e:
				time.sleep(5)
				count += 1
				print(f"Error occurred: {e}  Now Retrying, (attempt:{count}/{5}), url:{url}")
		else:
			print("Attempt 5 times is Out time")
			return False, into

	def down_save(self, img_url, byte_data):
		tag_dir = '+'.join(self.tags)
		if os.path.isdir(self.save_folder) == False:
			os.makedirs(self.save_folder)
			print(f"created new directory '{self.save_folder}'!")
		if os.path.isdir(f'{self.save_folder}/{self.save_name}/{tag_dir}') == False:
			os.makedirs(f'{self.save_folder}/{self.save_name}/{tag_dir}')
			print(f"created new directory '{tag_dir}'!")
		try:
			file_name = f"{self.save_folder}/{self.save_name}/{tag_dir}/{str(time.time())[:-4]}.{img_url.split('.')[-1]}"
			f = open(file_name, 'wb')
			f.write(byte_data)
			into = True
		except Exception as e:
			print(f"{e} {img_url}  an error occured!")
			into = False
		finally:
			f.close()
		return into

	def print_nowpid(self, url, pid, into):
		if not into:
			print("Url:", url, " Now pid:", pid, " Now page:", int((pid // 42) + 1), "--Error")
		else:
			print("Url:", url, " Now pid:", pid, " Now page:", int((pid // 42) + 1), "--Success")
		return pid + 1

	def download_main(self):
		down_url = self.url
		error_array = []
		self.conter_pid = self.pid_start
		print("start: ", self.conter_pid ,"   end:", self.pid_end)
		while (self.contentpresent(down_url) and self.conter_pid < self.pid_end):
			print(
				f'collecting images from page = {(self.conter_pid // self.page_size[self.name]) + 1} | pid = {self.conter_pid}')
			res = self.res_get(down_url)
			if not res:
				continue
			soup = BeautifulSoup(res, 'lxml')
			thumbnails = self.webname_findAll(soup)
			pid = self.conter_pid
			for i in thumbnails:
				link, into = self.download_link(i, down_url)
				if not into:
					error_array.append(link)
				pid = self.print_nowpid(link, pid, into)

			with open("error_url.txt", "a") as f:
				f.write("\n".join(error_array))

			self.conter_pid = self.conter_pid + self.page_size[self.name]
			down_url = self.get_url(self.conter_pid)

	def main(self):
		temp = 0
		while (True):
			if temp:
				self.chance_tags()
				self.chance_page()
			self.download_main()
			ch = input("Enter [c] to continue; else any other key to exit: ")
			if (ch.lower() != 'c'):
				break
			os.system('cls')
			temp += 1



if __name__ == '__main__':
	# web_name = "gelbooru"
	# web_name = "rule34"
	web_name = "blacked"
	# web_name = "xbooru"
	# web_name = "yande"
	
	D = Downloading(web_name)
	D.main()
