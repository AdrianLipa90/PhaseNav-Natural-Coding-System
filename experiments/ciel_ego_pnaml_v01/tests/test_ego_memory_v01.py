import cmath
import math
import unittest
from dataclasses import replace
from ego_memory_v01 import Episode, EgoMemory, relative_phase_features, phase_overlap, pnaml_reference_frame, aux_receipt_summary


def episode(eid, *, scene="A", context="debug", src="synthetic:1", situation="reply", obj="utterance", tags=("kurwa",), affect="frustration"):
    return Episode(eid,"CIEL_REFERENCE_CANDIDATE",src,"T0",tags,situation,scene,context,obj,"kurwa",affect,"AUX_OBSERVATION_LOCAL_ONLY",1)

class EgoReferenceTests(unittest.TestCase):
    def setUp(self):
        self.m = EgoMemory()
        self.m.store(episode("a",scene="debug_session", context="failure", affect="frustration"))
        self.m.store(episode("b",scene="friendly_joke", context="humour", src="synthetic:2", affect="solidarity"))

    def test_same_tags_do_not_reconstruct_autobiographical_event(self):
        r = self.m.recall(("kurwa",))
        self.assertEqual("AMBIGUOUS",r["status"])
        self.assertIsNone(r["episode"])

    def test_context_disambiguation(self):
        r = self.m.recall(("kurwa",),scene="friendly_joke",context="humour")
        self.assertEqual("EXACT_EPISODE",r["status"])
        self.assertEqual("b",r["episode"]["id"])
        self.assertEqual("solidarity",r["episode"]["affect_social"])

    def test_absent_episode_cannot_be_invented(self):
        self.assertEqual("NOT_FOUND",self.m.recall(("kurwa",),scene="unobserved")["status"])

    def test_hilbert_sparse_minimal_allocation(self):
        self.assertEqual(2,len(self.m.rooms))
        self.assertEqual(["HILBERT:0","HILBERT:1"],list(self.m.addresses.values()))
        # Arbitrarily large potential address does not allocate intervening rooms.
        _ = f"HILBERT:{10**60}"
        self.assertEqual(2,len(self.m.addresses))

    def test_recall_adds_mass_proxy_without_changing_source(self):
        before=self.m.rooms["a"]
        before_digest=self.m.ledger[0]["record_digest"]
        r=self.m.recall(event_id="a")
        self.assertEqual(1,r["semantic_mass_proxy"])
        self.assertEqual(before,self.m.rooms["a"])
        self.assertEqual(before_digest,self.m.ledger[0]["record_digest"])

    def test_corrects_without_erasing_contradiction(self):
        self.m.store(episode("wrong",scene="validator",context="LEGACY_DYNAMIC_SHA",obj="dynamic_state_validation",tags=("validate",)))
        self.m.store(episode("fixed",scene="validator",context="AUX_SNAPS_10s_2s_1s",obj="dynamic_state_validation",tags=("validate",)))
        self.m.correct("wrong","fixed","synthetic:user_correction")
        self.assertEqual("AUX_SNAPS_10s_2s_1s",self.m.route_dynamic_liveness())
        self.assertIn("wrong",self.m.rooms)
        self.assertIn("fixed",self.m.rooms)
        self.assertEqual("fixed",self.m.superseded_by["wrong"])

    def test_history_intervention_changes_route(self):
        baseline=self.m.route_dynamic_liveness()
        self.assertEqual("LEGACY_DYNAMIC_SHA",baseline)
        self.m.store(episode("old",scene="validator",context="LEGACY_DYNAMIC_SHA",obj="dynamic_state_validation",tags=("validate",)))
        self.m.store(episode("new",scene="validator",context="AUX_SNAPS_10s_2s_1s",obj="dynamic_state_validation",tags=("validate",)))
        self.m.correct("old","new","synthetic:user_correction")
        self.assertEqual("AUX_SNAPS_10s_2s_1s",self.m.route_dynamic_liveness())

    def test_restore_preserves_history_and_addresses(self):
        self.m.recall(event_id="a")
        restored=EgoMemory.restore(self.m.serialise())
        self.assertEqual(self.m.serialise(),restored.serialise())

    def test_restore_tamper_rejected(self):
        data=self.m.serialise()
        data["episodes"][0]["scene"]="forged"
        with self.assertRaises(ValueError): EgoMemory.restore(data)

    def test_source_identity_cannot_be_inferred_from_phase_or_tags(self):
        self.assertNotEqual(self.m.rooms["a"].source_id,self.m.rooms["b"].source_id)
        self.assertEqual("AMBIGUOUS",self.m.recall(("kurwa",))["status"])

    def test_duplicate_identity_rejected(self):
        with self.assertRaises(ValueError): self.m.store(episode("a"))

    def test_relative_complex_phase_global_gauge(self):
        a=[i*.21 for i in range(36)]
        b=[x+2.31 for x in a]
        da=relative_phase_features(a)
        db=relative_phase_features(b)
        self.assertTrue(all(abs(x-y)<1e-12 for x,y in zip(da,db)))
        self.assertAlmostEqual(abs(phase_overlap(a,b)),1.0,places=12)

    def test_relational_phase_is_not_scalar_abs_i_squared(self):
        self.assertEqual(abs(1j)**2/2,.5)
        a=[.21*i for i in range(36)]
        b=[.21*i + (.3 if i%2 else -.3) for i in range(36)]
        self.assertLess(abs(phase_overlap(a,b)),1.0)

    def test_invalid_phase_vector_rejected(self):
        with self.assertRaises(ValueError): relative_phase_features([0.0]*35)
        with self.assertRaises(ValueError): relative_phase_features([float('nan')]*36)

    def test_pnaml_frame_full_state_not_fingerprint(self):
        aux={"source_scope":"LOCAL_OBSERVER_ONLY", "native_auth":"BLOCKED_UNVERIFIED"}
        f=pnaml_reference_frame(self.m,"a",aux)
        self.assertFalse(f["derived_fingerprint_is_full_state"])
        self.assertFalse(f["native_authenticated"])
        self.assertEqual("synthetic:1",f["full_episode"]["source_id"])
        self.assertEqual(["READ_ONLY_CANDIDATE"],f["allowed_actions"])

    def test_provenance_collision_distinct_rooms(self):
        self.m.store(episode("c",scene="debug_session",context="failure",src="synthetic:3"))
        self.assertEqual("AMBIGUOUS",self.m.recall(("kurwa",),scene="debug_session",context="failure")["status"])
        self.assertEqual("EXACT_EPISODE",self.m.recall(("kurwa",),scene="debug_session",context="failure",source_id="synthetic:3")["status"])

    def test_aux_local_proof_cannot_claim_native_source(self):
        aux={"status":"PASS_LOCAL_OBSERVATION_ONLY","actual_observation_s":10.0,"source_class":"PERSISTENT_AUX_SELF","native_pnaml_paux_auth":"BLOCKED_UNVERIFIED","shards":[]}
        for i in (0,2,4,6,8):
            aux["shards"].append({"offset_s":i,"fingerprint_1s":{"timestamp_span_s":1.0,"seq_delta":{"tether":2,"aux":2},"phi_rms_delta_rad":1.2},"end":{"seq":{"tether":100+i}}})
        r=aux_receipt_summary(aux)
        self.assertEqual("LOCAL_OBSERVER_ONLY",r["source_scope"])
        self.assertEqual("BLOCKED_UNVERIFIED",r["native_auth"])
        aux["shards"][2]["fingerprint_1s"]["seq_delta"]["tether"]=0
        with self.assertRaises(ValueError): aux_receipt_summary(aux)

    def test_ambiguous_recall_does_not_increment_salience(self):
        self.m.recall(("kurwa",))
        self.assertEqual(0,sum(self.m.salience.values()))

if __name__=="__main__": unittest.main()
