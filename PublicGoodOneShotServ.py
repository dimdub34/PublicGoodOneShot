# -*- coding: utf-8 -*-

from twisted.internet import defer
import pandas as pd
import matplotlib.pyplot as plt
import logging
from collections import OrderedDict
from util import utiltools
import PublicGoodOneShotParams as pms
from PublicGoodOneShotTexts import trans_PGOS


logger = logging.getLogger("le2m".format(__name__))


class Serveur(object):
    def __init__(self, le2mserv):
        self._le2mserv = le2mserv

        # creation of the menu (will be placed in the "part" menu on the
        # server screen
        actions = OrderedDict()
        actions[trans_PGOS(u"Configure")] = self._configure
        actions[trans_PGOS(u"Display parameters")] = \
            lambda _: self._le2mserv.gestionnaire_graphique. \
            display_information2(
                utiltools.get_module_info(pms), u"Paramètres")
        actions[trans_PGOS(u"Start")] = lambda _: self._demarrer()
        actions[trans_PGOS(u"Display payoffs")] = \
            lambda _: self._le2mserv.gestionnaire_experience.\
            display_payoffs_onserver("PublicGoodOneShot")
        self._le2mserv.gestionnaire_graphique.add_topartmenu(
            u"Public Good Game", actions)

    def _configure(self):
        self._le2mserv.gestionnaire_graphique.display_information(
            trans_PGOS(u"There is no nothing to configure"))
        return

    @defer.inlineCallbacks
    def _demarrer(self):
        """
        Start the part
        :return:
        """
        # check conditions =====================================================
        if self._le2mserv.gestionnaire_joueurs.nombre_joueurs % \
                pms.TAILLE_GROUPES != 0 :
            self._le2mserv.gestionnaire_graphique.display_error(
                trans_PGOS(u"The number of players is not compatible "
                          u"with the group size"))
            return
        confirmation = self._le2mserv.gestionnaire_graphique.\
            question(u"Démarrer PublicGoodOneShot?")
        if not confirmation:
            return

        # init part ============================================================
        yield (self._le2mserv.gestionnaire_experience.init_part(
            "PublicGoodOneShot", "PartiePGOS", "RemotePGOS", pms))
        self._tous = self._le2mserv.gestionnaire_joueurs.get_players(
            'PublicGoodOneShot')

        # groups
        self._le2mserv.gestionnaire_groupes.former_groupes(
            self._le2mserv.gestionnaire_joueurs.get_players(),
            pms.TAILLE_GROUPES, forcer_nouveaux=True)

        # set parameters on remotes
        yield (self._le2mserv.gestionnaire_experience.run_func(
            self._tous, "configure"))

        # start ================================================================
        for period in range(1 if pms.NOMBRE_PERIODES else 0,
                        pms.NOMBRE_PERIODES + 1):

            if self._le2mserv.gestionnaire_experience.stop_repetitions:
                break

            # init period
            self._le2mserv.gestionnaire_graphique.infoserv(
                [None, u"Période {}".format(period)])
            self._le2mserv.gestionnaire_graphique.infoclt(
                [None, u"Période {}".format(period)], fg="white", bg="gray")
            yield (self._le2mserv.gestionnaire_experience.run_func(
                self._tous, "newperiod", period))
            
            # decision
            yield(self._le2mserv.gestionnaire_experience.run_step(
                u"Décision", self._tous, "display_decision"))

            # compute total amount in the public account by group
            self._le2mserv.gestionnaire_graphique.infoserv(
                trans_PGOS(u"Total amount by group"))
            for g, m in self._le2mserv.gestionnaire_groupes.get_groupes(
                    "PublicGoodOneShot").viewitems():
                total = sum([p.currentperiod.PGOS_public for p in m])
                for p in m:
                    p.currentperiod.PGOS_publicgroup = total
                self._le2mserv.gestionnaire_graphique.infoserv(
                    u"G{}: {}".format(g.split("_")[2], total))
            
            # period payoff
            self._le2mserv.gestionnaire_experience.compute_periodpayoffs(
                "PublicGoodOneShot")
        
            # summary
            yield(self._le2mserv.gestionnaire_experience.run_step(
                u"Summary", self._tous, "display_summary"))

        # end of part ==========================================================
        yield (self._le2mserv.gestionnaire_experience.finalize_part(
            "PublicGoodOneShot"))
