# -*- coding: utf-8 -*-

from twisted.internet import defer
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, Float, ForeignKey
import logging
from datetime import datetime
from util.utiltools import get_module_attributes
from server.servbase import Base
from server.servparties import Partie
import PublicGoodOneShotParams as pms


logger = logging.getLogger("le2m")


class PartiePGOS(Partie):
    __tablename__ = "partie_PublicGoodOneShot"
    __mapper_args__ = {'polymorphic_identity': 'PublicGoodGame'}
    partie_id = Column(Integer, ForeignKey('parties.id'), primary_key=True)
    repetitions = relationship('RepetitionsPGOS')

    def __init__(self, le2mserv, joueur):
        super(PartiePGOS, self).__init__("PublicGoodOneShot", "PGOS")
        self._le2mserv = le2mserv
        self.joueur = joueur
        self.PGOS_gain_ecus = 0
        self.PGOS_gain_euros = 0

    @defer.inlineCallbacks
    def configure(self, *args):
        logger.debug(u"{} Configure".format(self.joueur))
        yield (self.remote.callRemote("configure", get_module_attributes(pms)))

    @defer.inlineCallbacks
    def newperiod(self, period):
        """
        Create a new period and inform the remote
        If this is the first period then empty the historic
        :param period:
        :return:
        """
        logger.debug(u"{} New Period".format(self.joueur))
        self.currentperiod = RepetitionsPGOS(period)
        self.currentperiod.PGOS_group = self.joueur.groupe
        self._le2mserv.gestionnaire_base.ajouter(self.currentperiod)
        self.repetitions.append(self.currentperiod)
        yield (
            self.remote.callRemote("newperiod", period))
        logger.info(u"{} Ready for periode {}".format(self.joueur, period))

    @defer.inlineCallbacks
    def display_decision(self):
        """
        Display the decision screen on the remote
        Get back the decision
        :return:
        """
        logger.debug(u"{} Decision".format(self.joueur))
        debut = datetime.now()
        self.currentperiod.PGOS_public = \
            yield(
                self.remote.callRemote("display_decision"))
        self.currentperiod.PGOS_decisiontime = \
            (datetime.now() - debut).seconds
        self.currentperiod.PGOS_indiv = \
            pms.DOTATION - self.currentperiod.PGOS_public
        self.joueur.info(u"{}".format(
            self.currentperiod.PGOS_public))
        self.joueur.remove_waitmode()

    def compute_periodpayoff(self):
        """
        Compute the payoff for the period
        :return:
        """
        logger.debug(u"{} Period Payoff".format(self.joueur))
        self.currentperiod.PGOS_indivpayoff = self.currentperiod.PGOS_indiv * 1
        self.currentperiod.PGOS_publicpayoff = \
            self.currentperiod.PGOS_publicgroup * pms.MPCR
        self.currentperiod.PGOS_periodpayoff = \
            self.currentperiod.PGOS_indivpayoff + \
            self.currentperiod.PGOS_publicpayoff

        # cumulative payoff since the first period
        if self.currentperiod.PGOS_period < 2:
            self.currentperiod.PGOS_cumulativepayoff = \
                self.currentperiod.PGOS_periodpayoff
        else: 
            previousperiod = self.periods[
                self.currentperiod.PGOS_period - 1]
            self.currentperiod.PGOS_cumulativepayoff = \
                previousperiod.PGOS_cumulativepayoff + \
                self.currentperiod.PGOS_periodpayoff

        # we store the period in the self.periodes dictionnary
        self.periods[self.currentperiod.PGOS_period] = self.currentperiod

        logger.debug(u"{} Period Payoff {}".format(
            self.joueur, self.currentperiod.PGOS_periodpayoff))

    @defer.inlineCallbacks
    def display_summary(self, *args):
        logger.debug(u"{} Summary".format(self.joueur))
        yield(
            self.remote.callRemote(
                "display_summary", self.currentperiod.todict()))
        self.joueur.info("Ok")
        self.joueur.remove_waitmode()

    @defer.inlineCallbacks
    def compute_partpayoff(self):
        logger.debug(u"{} Part Payoff".format(self.joueur))

        self.PGOS_gain_ecus = \
            self.currentperiod.PGOS_cumulativepayoff
        self.PGOS_gain_euros = \
            float(self.PGOS_gain_ecus) * \
            float(pms.TAUX_CONVERSION)
        yield (self.remote.callRemote(
            "set_payoffs", self.PGOS_gain_euros, self.PGOS_gain_ecus))

        logger.info(u'{} Part Payoff ecus {} Part Payoff euros {:.2f}'.format(
            self.joueur, self.PGOS_gain_ecus, self.PGOS_gain_euros))


class RepetitionsPGOS(Base):
    __tablename__ = 'partie_PublicGoodOneShot_repetitions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    partie_partie_id = Column(
        Integer,
        ForeignKey("partie_PublicGoodOneShot.partie_id"))

    PGOS_period = Column(Integer)
    PGOS_treatment = Column(Integer)
    PGOS_group = Column(Integer)
    PGOS_indiv = Column(Integer)
    PGOS_public = Column(Integer)
    PGOS_publicgroup = Column(Integer)
    PGOS_decisiontime = Column(Integer)
    PGOS_indivpayoff = Column(Float)
    PGOS_publicpayoff = Column(Float)
    PGOS_periodpayoff = Column(Float)
    PGOS_cumulativepayoff = Column(Float)

    def __init__(self, periode):
        self.PGOS_treatment = pms.TREATMENT
        self.PGOS_period = periode
        self.PGOS_decisiontime = 0
        self.PGOS_periodpayoff = 0
        self.PGOS_cumulativepayoff = 0

    def todict(self, joueur=None):
        temp = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        if joueur:
            temp["joueur"] = joueur
        return temp
