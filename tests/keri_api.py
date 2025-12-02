from typing import List

from hio.base import doing, Doer
from hio.help import decking
from hio.help.decking import Deck
from keri import kering
from keri.app import habbing, oobiing
from keri.app.agenting import WitnessReceiptor, WitnessInquisitor
from keri.app.delegating import Anchorer
from keri.app.forwarding import Poster
from keri.app.habbing import Habery, Hab, GroupHab
from keri.core import serdering, coring
from keri.core.coring import Seqner
from keri.db import basing, dbing
from keri.db.basing import Baser
from keri.help import helping


def delegate_confirm_single_sig(del_deeds, dgt_deeds, wit_deeds):
    """
    Perform single sig delegation approval; equivalent of `kli delegate confirm`
    Uses deeds created from a Doist in the context of a test.
    """

class HabHelpers:
    @staticmethod
    def generate_oobi(hby: habbing.Habery, alias: str = None, role: str = kering.Roles.witness):
        hab = hby.habByName(name=alias)
        oobi = ''
        if role in (kering.Roles.witness,):
            if not hab.kever.wits:
                raise kering.ConfigurationError(f"{alias} identifier {hab.pre} does not have any witnesses.")
            for wit in hab.kever.wits:
                urls = hab.fetchUrls(eid=wit, scheme=kering.Schemes.http) \
                       or hab.fetchUrls(eid=wit, scheme=kering.Schemes.https)
                if not urls:
                    raise kering.ConfigurationError(f"unable to query witness {wit}, no http endpoint")

                url = urls[kering.Schemes.https] if kering.Schemes.https in urls else urls[kering.Schemes.http]
                oobi = f"{url.rstrip("/")}/oobi/{hab.pre}/witness"
        elif role in (kering.Roles.controller,):
            urls = hab.fetchUrls(eid=hab.pre, scheme=kering.Schemes.http) \
                   or hab.fetchUrls(eid=hab.pre, scheme=kering.Schemes.https)
            if not urls:
                raise kering.ConfigurationError(f"{alias} identifier {hab.pre} does not have any controller endpoints")
            url = urls[kering.Schemes.https] if kering.Schemes.https in urls else urls[kering.Schemes.http]
            oobi = f"{url.rstrip("/")}/oobi/{hab.pre}/controller"
        elif role in (kering.Roles.mailbox,):
            for (_, _, eid), end in hab.db.ends.getItemIter(keys=(hab.pre, kering.Roles.mailbox, )):
                if not (end.allowed and end.enabled is not False):
                    continue

                urls = hab.fetchUrls(eid=eid, scheme=kering.Schemes.http) or hab.fetchUrls(eid=hab.pre,
                                                                                           scheme=kering.Schemes.https)
                if not urls:
                    raise kering.ConfigurationError(f"{alias} identifier {hab.pre} does not have any mailbox endpoints")
                url = urls[kering.Schemes.https] if kering.Schemes.https in urls else urls[kering.Schemes.http]
                oobi = f"{url.rstrip("/")}/oobi/{hab.pre}/mailbox/{eid}"
        if oobi:
            return oobi
        else:
            raise kering.ConfigurationError(f"Unable to generate OOBI for {alias} identifier {hab.pre} with role {role}")

    @staticmethod
    def resolve_wit_oobi(doist: doing.Doist, wit_deeds: List[Doer], hby: habbing.Habery, oobi: str, alias: str = None):
        """Resolve an OOBI depending on a given witness for a given Habery."""
        obr = basing.OobiRecord(date=helping.nowIso8601())
        if alias is not None:
            obr.oobialias = alias
        hby.db.oobis.put(keys=(oobi,), val=obr)

        oobiery = oobiing.Oobiery(hby=hby)
        authn = oobiing.Authenticator(hby=hby)
        oobiery_deeds = doist.enter(doers=oobiery.doers + authn.doers)
        while not oobiery.hby.db.roobi.get(keys=(oobi,)):
            doist.recur(deeds=decking.Deck(wit_deeds + oobiery_deeds))
            hby.kvy.processEscrows()  # process any escrows from witness receipts

    @staticmethod
    def has_delegables(db: Baser):
        dlgs = []
        for (pre, sn), edig in db.delegables.getItemIter():
            dlgs.append((pre, sn, edig))
        return dlgs

class DelegationAutoApprover(doing.Doer):
    """
    Automatically approves delegation requests for testing purposes.
    """
    def __init__(self):
        super(DelegationAutoApprover, self).__init__()

    def recur(self, tock=0.0, **opts):
        pass


class Dipper(doing.DoDoer):
    """
    Handles the delegation lifecycle for single-sig identifiers from the perspective of the delegate.

    Assumes the delegate Hab is already made and that only witness receipts, delegation approval, and
    waiting for completion are needed.

    TODO add 2FA witness support (auths)
    """
    def __init__(self, hby: Habery, hab: Hab, proxy: str = None):
        """
        Constructs the subtasks for Dipper. Assumes the delegate Hab is already created.
        Adds a witness receiptor if the delegate is using witnesses.
        Assumes something else is running the HaberyDoer, Poster, and MailboxDirector

        TODO maybe witReceiptor and receiptor are not needed since the Anchorer makes its own?
        """
        self.hby = hby
        self.hab = hab
        self.proxy = self.hby.habByName(proxy) if proxy is not None else None
        self.sender = proxy if proxy is not None else hab
        self.postman = Poster(hby=self.hby)
        self.cues = decking.Deck()

        # Doers - async tasks
        self.anchorer = Anchorer(hby=self.hby, proxy=self.proxy)
        self.icpCompleter = DipSender(self.anchorer, self.hab, self.cues)
        self.witReceiptor = WitnessReceiptor(hby=self.hby)
        self.receiptWaiter = ReceiptWaiter(pre=self.hab.pre, sn=0, cues=self.cues, witReceiptor = self.witReceiptor)
        self.dipSender = DipPublisher(hab=self.hab, proxy=self.proxy, cues=self.cues, postman=self.postman)
        doers: List[Doer] = [self.anchorer, self.icpCompleter, self.witReceiptor, self.postman, self.dipSender]
        if hab.kever.wits:
            doers.append(self.receiptWaiter)
        super(Dipper, self).__init__(doers=doers)

    def recur(self, tyme, deeds=None):
        """Consumes dipSent and cleans up doers, completing this DoDoer."""
        super(Dipper, self).recur(tyme, deeds=deeds)  # plumbing call to DoDoer superclass - required
        while self.cues:
            cue = self.cues.popleft()
            kin = cue.get("kin", "")
            if kin == "delComplete":
                self.cues.append({'kin': 'rctWait'})
                return False  # wait on receipts - not done yet
            elif kin == "rctComplete":
                self.cues.append({'kin': 'dipPublish'})
                return False  # publish dip - not done yet
            elif kin == "dipSent":
                print(f"Delegated inception process complete for {self.hab.pre}.")
                self.remove(self.doers)  # remove any remaining doers
                return True  # done
            else:
                self.cues.append(cue)
            return False  # not done yet
        return False  # not done yet

class DipSender(doing.Doer):
    """
    Uses Anchorer to create and send the "dip" event and waits for delegation approval.
    """
    def __init__(self, anchorer: Anchorer, hab: Hab, cues: Deck):
        self.anchorer = anchorer
        self.hab = hab
        self.cues = cues
        super(DipSender, self).__init__()

    def start_delegation_and_wait(self):
        """
        Creates the delegation, sends it to the delegator using Anchorer, and
        publishes delComplete after delegation approval.
        """
        self.anchorer.delegation(pre=self.hab.pre, sn=0)
        print(f"Waiting for delegation approval for {self.hab.kever.prefixer.qb64}...")
        while not self.anchorer.complete(self.hab.kever.prefixer, Seqner(sn=self.hab.kever.sn)):
            yield self.tock
        print(f"Delegation approved for {self.hab.kever.prefixer.qb64}, cueing completion.")
        self.cues.append({'kin': 'delComplete', 'pre': self.hab.pre})

    def recur(self, tock=0.0, **opts):
        yield from self.start_delegation_and_wait()
        return True

class ReceiptWaiter(doing.Doer):
    """
    Waits for a receiptor to finish receipting and then publishes a receipt completion cue.
    """
    def __init__(self, pre: str, sn: int, cues: decking.Deck, witReceiptor: WitnessReceiptor):
        self.pre = pre
        self.sn = sn
        self.cues = cues
        self.witReceiptor = witReceiptor
        super(ReceiptWaiter, self).__init__()

    def waitOnReceipts(self):
        """
        Uses Receiptor or WitnessReceiptor to propagate receipts to witnesses.
        Publishes rctComplete.
        """
        self.witReceiptor.msgs.append(dict(pre=self.pre))
        while not self.witReceiptor.cues:
            _ = yield self.tock
        print(f"Receipts obtained for {self.pre} at sn {self.sn}, cueing completion.")
        self.cues.append({'kin': 'rctComplete', 'pre': self.pre, 'sn': self.sn})

    def recur(self, tock=0.0, **opts):
        """Consumes rctWait cue and waits on receipts."""
        while True:
            while self.cues:
                cue = self.cues.popleft()
                cueKin = cue["kin"]
                if cueKin == "rctWait":
                    yield from self.waitOnReceipts()
                    return True
                else:
                    self.cues.append(cue)
                yield tock
            yield tock

class DipPublisher(doing.Doer):
    """
    Sends the delegated inception event to the delegator.
    """
    def __init__(self, hab: Hab, proxy: Hab, cues: Deck, postman: Poster):
        self.hab = hab
        self.sender = proxy if proxy is not None else hab
        self.cues = cues
        self.postman = postman
        super(DipPublisher, self).__init__()

    def sendDip(self):
        """Publishes dipSent after sending the "dip" to the delegator."""
        print(f"Sending delegated inception event for {self.hab.pre} to delegator...")
        yield from self.postman.sendEventToDelegator(
            sender=self.sender,
            hab=self.hab,
            fn=self.hab.kever.sn)
        self.cues.append({'kin': 'dipSent', 'pre': self.hab.pre})

    def recur(self, tock=0.0, **opts):
        """Consumes dipPublish and sends the delegated inception event."""
        while True:
            while self.cues:
                cue = self.cues.popleft()
                cueKin = cue["kin"]
                if cueKin == "dipPublish":
                    yield from self.sendDip()
                    return True
                else:
                    self.cues.append(cue)
                yield tock
            yield tock


class DipSealer(doing.DoDoer):
    """
    Equivalent of `kli delegate confirm` for single-sig delegation approval in tests.
    Handles the delegation approval lifecycle for single-sig delegators approving single-sig delegation requests.
    Assumes all delegation requests are to be approved automatically.

    TODO add 2FA witness support (auths)
    """
    def __init__(self, hby:Habery, hab: Hab, witRcptrDoer: WitnessReceiptor, interact: bool = True):
        self.hby = hby
        self.hab = hab
        self.interact = interact
        self.cues = decking.Deck()

        # TODO add group delegation support
        # Counselor (group only)
        # Multiplexor (group only)

        # Doers - async tasks
        self.witInquisitor = WitnessInquisitor(hby=self.hby)
        self.witRcptrDoer = witRcptrDoer
        self.approver = DelegableApprover(hby=hby, hab=hab, interact=interact, witRcptr=witRcptrDoer, witq=self.witInquisitor, cues=self.cues)
        self.toRemove: List[Doer] = [self.witInquisitor, self.approver]

        super(DipSealer, self).__init__(doers=[self.witInquisitor, self.approver])

    def recur(self, tyme, deeds=None):
        while self.cues:
            cue = self.cues.popleft()
            kin = cue.get("kin", "")
            if kin == "approvalComplete":
                print(f"Delegation approval process complete for {cue.get('pre')}.")
                self.remove(self.toRemove)  # remove any remaining doers
                return True  # done
            else:
                self.cues.append(cue)
            break  # not done yet
        super(DipSealer, self).recur(tyme, deeds=deeds)  # plumbing call to DoDoer superclass - required

    def delegablesEscrowed(self):
        return [(pre, sn, edig) for (pre, sn), edig in self.hby.db.delegables.getItemIter()]

class DelegableApprover(Doer):
    """Checks the delegables escrow and auto-approves them, cueing up either the receipt process or event confirmation."""
    def __init__(self, hby: Habery, hab: Hab, interact: bool, witRcptr: WitnessReceiptor, witq: WitnessInquisitor, cues: Deck):
        self.hby = hby
        self.hab = hab
        self.interact = interact
        self.witRcptr = witRcptr
        self.witq = witq
        self.cues = cues
        super(DelegableApprover, self).__init__()

    def delegablesEscrowed(self):
        return [(pre, sn, edig) for (pre, sn), edig in self.hby.db.delegables.getItemIter()]

    def recur(self, tock=0.0, **opts):
        self.tock = tock
        _ = (yield self.tock)

        while True:
            dlgs = self.delegablesEscrowed()
            if len(dlgs) == 0:
                yield self.tock  # no delegables to process - task is not done and should run forever
            for pre, sn, edig in dlgs:
                dgkey = dbing.dgKey(pre, edig)
                eraw = self.hby.db.getEvt(dgkey)
                if eraw is None:
                    continue
                eserder = serdering.SerderKERI(raw=bytes(eraw))  # escrowed event

                ilk = eserder.sad["t"]
                if ilk in (coring.Ilks.dip,):
                    delpre = eserder.sad["di"]
                elif ilk in (coring.Ilks.drt,):
                    dkever = self.hby.kevers[eserder.pre]
                    delpre = dkever.delpre
                else:
                    continue

                if delpre not in self.hby.prefixes:  # I am the delegator
                    raise kering.KeriError(f"Delegator {delpre} not found in Habery.")
                hab = self.hby.habs[delpre]

                if isinstance(hab, GroupHab):
                    raise kering.ConfigurationError("Group delegation not supported in DipSealer.")

                cur = hab.kever.sner.num
                anchor = dict(i=eserder.ked['i'], s=eserder.snh, d=eserder.said)
                if self.interact:
                    hab.interact(data=[anchor])
                else:
                    hab.rotate(data=[anchor])

                # WitnessReceiptor is handled by the outer test context
                if hab.kever.wits:
                    witMsg = dict(pre=hab.pre, sn=cur+1)
                    self.witRcptr.msgs.append({'kin': 'eventToWitness', 'pre': hab.pre, 'sn': cur+1, 'witMsg': witMsg})
                    while not self.witRcptr.cues:
                        yield self.tock
                print(f'Delegagtor Prefix {hab.pre}')
                print(f'\tDelegate {ilk} event {eserder.pre} Anchored at Seq. No. {hab.kever.sner.num}')

                # wait for confirmation of fully commited event
                if eserder.pre in self.hby.kevers:
                    self.witq.query(src=hab.pre, pre=eserder.pre, sn=eserder.sn)
                    while eserder.sn < self.hby.kevers[eserder.pre].sn:
                        yield self.tock
                else:  # It should be an inception event then...
                    wits = [werfer.qb64 for werfer in eserder.berfers]
                    self.witq.query(src=hab.pre, pre=eserder.pre, sn=eserder.sn, wits=wits)
                    while eserder.pre not in self.hby.kevers:
                        yield self.tock

                print(f"Delegate {ilk} event {eserder.pre} committed.")

                self.hby.db.delegables.rem(keys=(pre, sn), val=edig)
                self.cues.append({'kin': 'approvalComplete', 'pre': eserder.ked['i']})
                return True