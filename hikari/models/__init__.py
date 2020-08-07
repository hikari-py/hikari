# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Data classes representing Discord entities."""

from hikari.models import applications
from hikari.models import audit_logs
from hikari.models import channels
from hikari.models import colors
from hikari.models import colours
from hikari.models import embeds
from hikari.models import emojis
from hikari.models import gateway
from hikari.models import guilds
from hikari.models import intents
from hikari.models import invites
from hikari.models import messages
from hikari.models import permissions
from hikari.models import presences
from hikari.models import users
from hikari.models import voices
from hikari.models import webhooks
from hikari.models.applications import *
from hikari.models.audit_logs import *
from hikari.models.channels import *
from hikari.models.colors import *
from hikari.models.colours import *
from hikari.models.embeds import *
from hikari.models.emojis import *
from hikari.models.gateway import *
from hikari.models.guilds import *
from hikari.models.intents import *
from hikari.models.invites import *
from hikari.models.messages import *
from hikari.models.permissions import *
from hikari.models.presences import *
from hikari.models.users import *
from hikari.models.voices import *
from hikari.models.webhooks import *

__all__ = (
    applications.__all__
    + audit_logs.__all__
    + channels.__all__
    + colors.__all__
    + colours.__all__
    + embeds.__all__
    + emojis.__all__
    + gateway.__all__
    + guilds.__all__
    + intents.__all__
    + invites.__all__
    + messages.__all__
    + permissions.__all__
    + presences.__all__
    + users.__all__
    + voices.__all__
    + webhooks.__all__
)
