# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: http://code.google.com/p/sickbeard/
#
# This file is part of Sick Beard.
#
# Sick Beard is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Sick Beard is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with Sick Beard.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import with_statement

import traceback

from lib.tvnamer.utils import FileParser
from lib.tvnamer import tvnamer_exceptions

import sickbeard

from common import *

from sickbeard import logger
from sickbeard import sab
from sickbeard import history

from sickbeard import notifiers 
from sickbeard import exceptions

from sickbeard.providers import *
from sickbeard import providers

def _downloadResult(result):

	resProvider = providers.getProviderModule(result.provider)

	newResult = False

	if resProvider == None:
		logger.log("Invalid provider name - this is a coding error, report it please", logger.ERROR)
		return False

	if resProvider.providerType == "nzb":
		newResult = resProvider.downloadNZB(result)
	elif resProvider.providerType == "torrent":
		newResult = resProvider.downloadTorrent(result)
	else:
		logger.log("Invalid provider type - this is a coding error, report it please", logger.ERROR)
		return False

	return newResult

def snatchEpisode(result, endStatus=SNATCHED):

	if result.resultType == "nzb":
		if sickbeard.NZB_METHOD == "blackhole":
			dlResult = _downloadResult(result)
		elif sickbeard.NZB_METHOD == "sabnzbd":
			dlResult = sab.sendNZB(result)
		else:
			logger.log("Unknown NZB action specified in config: " + sickbeard.NZB_METHOD, logger.ERROR)
			dlResult = False
	elif result.resultType == "torrent":
		dlResult = _downloadResult(result)
	else:
		logger.log("Unknown result type, unable to download it", logger.ERROR)
		dlResult = False
	
	if dlResult == False:
		return

	history.logSnatch(result)

	# don't notify when we snatch a backlog episode, that's just annoying
	if endStatus != SNATCHED_BACKLOG:
		notifiers.notify(NOTIFY_SNATCH, result.episode.prettyName(True))
	
	with result.episode.lock:
		if result.predownloaded == True:
			logger.log("changing status from " + str(result.episode.status) + " to " + str(PREDOWNLOADED), logger.DEBUG)
			result.episode.status = PREDOWNLOADED
		else:
			logger.log("changing status from " + str(result.episode.status) + " to " + str(endStatus), logger.DEBUG)
			result.episode.status = endStatus
		result.episode.saveToDB()

	sickbeard.updateMissingList()
	sickbeard.updateAiringList()
	sickbeard.updateComingList()

def _doSearch(episode, provider, manualSearch):

	# if we already got the SD then only try HD on BEST episodes
	if episode.show.quality == BEST and episode.status == PREDOWNLOADED:
		foundEps = provider.findEpisode(episode, HD, manualSearch)
	else:
		foundEps = provider.findEpisode(episode, manualSearch=manualSearch)

	# if we found something and we're on BEST, retry to see if we can guarantee HD.
	if len(foundEps) > 0 and episode.show.quality == BEST and episode.status != PREDOWNLOADED:
			moreFoundEps = provider.findEpisode(episode, HD, manualSearch)
			
			# if we couldn't find a definitive HD version then mark the original ones as predownloaded
			if len(moreFoundEps) == 0:
				for curResult in foundEps:
					curResult.predownloaded = True
			else:
				return moreFoundEps

	return foundEps

def findEpisode(episode, manualSearch=False):

	logger.log("Searching for " + episode.prettyName(True))

	foundEps = []

	didSearch = False

	for curProvider in providers.getAllModules():
		
		if not curProvider.isActive():
			continue
		
		try:
			foundEps = _doSearch(episode, curProvider, manualSearch)
		except exceptions.AuthException, e:
			logger.log("Authentication error: "+str(e), logger.ERROR)
			continue
		except Exception, e:
			logger.log("Error while searching "+curProvider.providerName+", skipping: "+str(e), logger.ERROR)
			logger.log(traceback.format_exc(), logger.DEBUG)
			continue
		
		didSearch = True
		
		if len(foundEps) > 0:
			break
	
	if not didSearch:
		logger.log("No providers were used for the search - check your settings and ensure that either NZB/Torrents is selected and at least one NZB provider is being used.", logger.ERROR)
	
	return foundEps
