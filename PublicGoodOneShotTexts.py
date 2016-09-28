# -*- coding: utf-8 -*-
"""
Ce module contient les textes des écrans
"""
__author__ = "Dimitri DUBOIS"

import os
import configuration.configparam as params
from collections import namedtuple
from util.utiltools import get_pluriel
import PublicGoodOneShotParams as pms
import gettext


localedir = os.path.join(params.getp("PARTSDIR"), "PublicGoodGame", "locale")
trans_PGOS = gettext.translation(
    "PublicGoodGame", localedir, languages=[params.getp("LANG")]).ugettext


TITLE_MSG = namedtuple("TITLE_MSG", "titre message")


def get_histo_head():
    return [trans_PGOS(u"Individual\naccount"),
            trans_PGOS(u"Public\naccount"), trans_PGOS(u"Public\naccount\ngroup"),
            trans_PGOS(u"Payoff")]


def get_text_explanation():
    return trans_PGOS(u"You have an endowment of {} tokens.").format(pms.DOTATION)


def get_text_label_decision():
    return trans_PGOS(u"Please enter the number of token(s) you put on the "
                     u"public account")


def get_text_summary(period_content):
    txt = trans_PGOS(u"You put {} in your individual account and {} in the "
                    u"public account. Your group put {} in the public "
                    u"account.\nYour payoff is equal "
                    u"to {}.").format(
        get_pluriel(period_content.get("PGOS_indiv"), trans_PGOS(u"token")),
        get_pluriel(period_content.get("PGOS_public"), trans_PGOS(u"token")),
        get_pluriel(period_content.get("PGOS_publicgroup"), trans_PGOS(u"token")),
        get_pluriel(period_content.get("PGOS_periodpayoff"), pms.MONNAIE))
    return txt

