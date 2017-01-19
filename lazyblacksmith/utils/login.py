# -*- encoding: utf-8 -*-
from flask import flash
from flask_login import login_user
from sqlalchemy.orm.exc import NoResultFound

from lazyblacksmith.models import Skill
from lazyblacksmith.models import User
from lazyblacksmith.models import UserPreference
from lazyblacksmith.models import db
from lazyblacksmith.tasks.character_skills import update_character_skills

import logging

logger = logging.getLogger("%s.utils.login" % __name__)


def check_login_user(cdata, auth_response, main=None):
    try:
        user = User.query.filter(
            User.character_id == cdata['CharacterID'],
            User.character_owner_hash == cdata['CharacterOwnerHash']
        ).one()

    except NoResultFound:
        # if none is found, try to find just with characterID
        try:
            user = User.query.filter(
                User.character_id == cdata['CharacterID'],
            ).one()
            # if no exception is triggered, it mean we have a registered charID
            # but with another account: owner has changed, we'll wipe all data.
            wipe_character_data(user)

        except NoResultFound:
            user = User()
            user.character_id = cdata['CharacterID']

    user.character_owner_hash = cdata['CharacterOwnerHash']
    user.character_name = cdata['CharacterName']
    user.update_token(auth_response)

    if main is not None:
        user.main_character = main

    try:
        db.session.merge(user)
        db.session.commit()
        update_data(user)

        if main is None:
            login_user(user)
            flash('You have successfully logged in.', 'success')
        else:
            flash(
                'You have successfully added "%s" to your alts list' % (
                    user.character_name,
                ), 'success'
            )

    except:
        logger.exception("Cannot login the user - uid: %d" % user.character_id)
        db.session.rollback()
        flash('Something went wrong. Please try to login again', 'error')


def wipe_character_data(user):
    Skill.query.filter(Skill.character_id == user.character_id).delete()
    db.session.commit()


def update_data(user):
    try:
        update_character_skills.s(user.character_id).apply_async()
    except:
        logger.exception("Cannot update skills")

    if not user.pref and not user.main_character:
        try:
            prefs = UserPreference()
            prefs.user = user
            db.session.merge(prefs)
            db.session.commit()
        except:
            logger.exception("Failed to initialize user preference")
            db.session.rollback()