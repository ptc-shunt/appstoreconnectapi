import requests
import jwt
from datetime import datetime, timedelta
import time
import json
from enum import Enum

ALGORITHM = 'ES256'
BASE_API = "https://api.appstoreconnect.apple.com"

class HttpMethod(Enum):
	GET = 1
	POST = 2
	PATCH = 3

class Api:

	def __init__(self, key_id, key_file, issuer_id):
		self._token = None
		self.token_gen_date = None
		self.exp = None
		self.key_id = key_id
		self.key_file = key_file
		self.issuer_id = issuer_id
		token = self.token  # generate first token

	def _generate_token(self):
		key = open(self.key_file, 'r').read()
		self.token_gen_date = datetime.now()
		exp = int(time.mktime((self.token_gen_date + timedelta(minutes=20)).timetuple()))
		return jwt.encode({'iss': self.issuer_id, 'exp': exp, 'aud': 'appstoreconnect-v1'}, key,
		                   headers={'kid': self.key_id, 'typ': 'JWT'}, algorithm=ALGORITHM).decode('ascii')

	def _api_call(self, route, method, post_data):
		headers = {"Authorization": "Bearer %s" % self.token}
		url = "%s%s" % (BASE_API, route)
		r = {}

		print(url)
		if method == HttpMethod.GET:
			r = requests.get(url, headers=headers)
		elif method == HttpMethod.POST:
			headers["Content-Type"] = "application/json"
			r = requests.post(url=url, headers=headers, data=json.dumps(post_data))
		elif method == HttpMethod.PATCH:
			headers["Content-Type"] = "application/json"
			r = requests.patch(url=url, headers=headers, data=json.dumps(post_data))

		if r.status_code in range(200,299):
			return r.json()
		else:
			print("Error [%d][%s]" % (r.status_code, r.content))
			return r

	#apps

	def apps(self):
		return self._api_call("/v1/apps", HttpMethod.GET, None)

	#users

	def users(self):
		return self._api_call("/v1/users", HttpMethod.GET, None)

	#userInvitations

	def user_invitations(self):
		return self._api_call("/v1/userInvitations", HttpMethod.GET, None)

	#betaGroups

	def beta_groups(self, app_id):
		return self._api_call("/v1/apps/" + app_id + "/betaGroups", HttpMethod.GET, None)

	def create_beta_group(self, group_name, app_id):
		post_data = {'data': {'attributes': {'name': group_name}, 'relationships': {'app': {'data': {'id': app_id, 'type': 'apps'}}}, 'type': 'betaGroups'}}

		return self._api_call("/v1/betaGroups", HttpMethod.POST, post_data)

	def beta_group_info(self, beta_group_id):
		return self._api_call("/v1/betaGroups/" + beta_group_id, HttpMethod.GET, None)

	#betaTesters

	def beta_testers(self):
		return self._api_call("/v1/betaTesters", HttpMethod.GET, None)

	def create_beta_tester(self, beta_group_id, email, first_name, last_name):
		post_data = {'data': {'attributes': {'email': email, 'firstName': first_name, 'lastName': last_name}, 'relationships': {'betaGroups': {'data': [{ 'id': beta_group_id ,'type': 'betaGroups'}]}}, 'type': 'betaTesters'}}

		return self._api_call("/v1/betaTesters", HttpMethod.POST, post_data)

	def beta_group_beta_testers(self, beta_group_id):
		return self._api_call("/v1/betaGroups/" + beta_group_id + "/betaTesters", HttpMethod.GET, None)

	#builds

	def builds(self):
		return self._api_call("/v1/builds", HttpMethod.GET, None)

	def build_processing_state(self, app_id, version):
		return self._api_call("/v1/builds?filter[app]=" + app_id + "&filter[version]=" + version + "&fields[builds]=processingState", HttpMethod.GET, None)

	def set_uses_non_encryption_exemption_setting(self, build_id, uses_non_encryption_exemption_setting):
		post_data = {'data': {'attributes': {'usesNonExemptEncryption': uses_non_encryption_exemption_setting}, 'id': build_id, 'type': 'builds'}}
		return self._api_call("/v1/builds/" + build_id, HttpMethod.PATCH, post_data)

	#betaAppReviewSubmissions

	def submit_app_for_beta_review(self, build_id):
		post_data = {'data': { 'type': 'betaAppReviewSubmissions', 'relationships': {'build': {'data': {'id': build_id, 'type': 'builds'}}}}}
		return self._api_call("/v1/betaAppReviewSubmissions", HttpMethod.POST, post_data)

	@property
	def token(self):
		# generate a new token every 15 minutes
		if not self._token or self.token_gen_date + timedelta(minutes=15) > datetime.now():
			self._token = self._generate_token()

		return self._token
