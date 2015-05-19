# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

from datetime import datetime

from sqlalchemy.dialects.postgresql import ARRAY

from indico.core.db import db
from indico.core.db.sqlalchemy import UTCDateTime
from indico.util.string import return_ascii
from MaKaC.common.cache import GenericCache


class OAuthToken(db.Model):
    """OAuth tokens"""

    __tablename__ = 'tokens'
    __table_args__ = ({'schema': 'oauth'})

    #: the unique identifier of the token
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: the identifier of the linked application
    application_id = db.Column(
        db.Integer,
        db.ForeignKey('oauth.applications.id'),
        nullable=False
    )
    #: the identifier of the linke user
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.users.id'),
        nullable=False,
        index=True
    )
    #: an unguessable unique string of characters
    access_token = db.Column(
        db.String,
        unique=True,
        nullable=False
    )
    #: the list of scopes the linked application may request access to
    scopes = db.Column(
        ARRAY(db.String)
    )
    #: the last time the token was used by the application
    last_used_dt = db.Column(
        UTCDateTime,
        nullable=True
    )
    #: application authorized by this token
    application = db.relationship('OAuthApplication')
    #: the user who owns this token
    user = db.relationship('User')

    @property
    def locator(self):
        return {'id': self.id}

    @property
    def type(self):
        return 'bearer'

    @return_ascii
    def __repr__(self):
        return '<OAuthToken({}, {}, {})>'.format(self.id, self.application, self.user)


class OAuthGrant(object):
    """OAuth grant token"""

    #: cache entry to store grant tokens
    _cache = GenericCache('oauth-grant-tokens')

    def __init__(self, client_id, code, redirect_uri, user, expires):
        self.client_id = client_id
        self.code = code
        self.redirect_uri = redirect_uri
        self.user = user
        self.scopes = ''
        self.expires = expires

    @property
    def key(self):
        return self.make_key(self.client_id, self.code)

    @property
    def ttl(self):
        return self.expires - datetime.nowutc()

    @classmethod
    def get(cls, client_id, code):
        key = cls.make_key(client_id, code)
        return cls._cache.get(key)

    @classmethod
    def make_key(cls, client_id, code):
        return '{}:{}'.format(client_id, code)

    def save(self):
        self._cache.set(key=self.key, value=self, time=self.ttl)

    def delete(self):
        self._cache.delete(self.key)
