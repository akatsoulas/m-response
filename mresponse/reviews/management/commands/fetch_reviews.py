import logging
from datetime import datetime, timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

import pytz
from mozapkpublisher.common.googleplay import _connect
from mresponse.applications.models import Application
from mresponse.reviews.models import Review

logger = logging.getLogger('mresponse.reviews.fetch_reviews')


class Command(BaseCommand):
    help = "Fetches all available reviews from Google playstore"

    @transaction.atomic
    def get_reviews(self, application):
        logger.info("Fetching new reviews for application: %s", application)
        service = _connect(settings.PLAY_ACCOUNT, settings.PLAY_CREDENTIALS_PATH)
        reviews_service = service.reviews()
        results = reviews_service.list(packageName=application.package).execute()

        while results:
            time_of_last_review = None

            for review in results['reviews']:
                # Reviews are returned in reverse-chronological order so this import
                # can stop importing when it reaches a target date/time. This target is
                # either the date/time of the most review we've imported before or one
                # week ago, which ever is closer to the current time.

                # Stop when we reach a review that's already imported
                if Review.objects.filter(play_store_review_id=review['reviewId']).exists():
                    return

                if len(review['comments']) == 1:
                    comment = review['comments'][0]['userComment']
                    kwargs = {
                        'play_store_review_id': review['reviewId'],
                        'android_sdk_version': comment.get('androidOsVersion'),
                        'author_name': review.get('authorName', ''),
                        'review_text': comment['text'],
                        'review_language': comment['reviewerLanguage'],
                        'review_rating': comment['starRating'],
                        'last_modified': timezone.make_aware(datetime.fromtimestamp(
                            int(comment['lastModified']['seconds'])
                        ), pytz.UTC)
                    }

                    # Stop when we reach a review that's older than one week
                    if kwargs['last_modified'] < timezone.now() - timedelta(days=7):
                        return

                    obj = Review(**kwargs)
                    obj.application = application
                    obj.save()

                    time_of_last_review = kwargs['last_modified']

            if len(results['reviews']) > 0:
                logger.info("Fetched %d reviews (%s)", len(results['reviews']), time_of_last_review)
            else:
                logger.info("Fetched 0 reviews")

            if results['tokenPagination']['nextPageToken']:
                nextPageToken = results['tokenPagination']['nextPageToken']
                results = reviews_service.list(
                    packageName=application.package, token=nextPageToken
                ).execute()
            else:
                break

    def handle(self, *args, **kwargs):
        for application in Application.objects.all():
            self.get_reviews(application)