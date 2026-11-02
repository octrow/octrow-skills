import Spec.Feed.Model
/-! Properties. Statements are frozen once the user approves them; only proofs change. -/
namespace Feed

theorem lt_trans {a b c : Post} (h₁ : lt a b = true) (h₂ : lt b c = true) : lt a c = true := by
  simp [lt] at *; omega

/-- The runtime check is sound: if it passes, the invariant holds. -/
theorem checkInv_sound (posts : List Post) (h : checkInv posts = true) : Inv posts := by
  fun_induction checkInv posts with
  | case1 a b rest ih =>
    simp only [Bool.and_eq_true] at h
    have tail := ih h.2
    refine List.Pairwise.cons ?_ tail
    intro c hc
    rcases List.mem_cons.mp hc with rfl | hc
    · exact h.1
    · exact lt_trans h.1 (List.rel_of_pairwise_cons tail hc)
  | case2 t hne =>
    match t, hne with
    | [], _ => simp [Inv]
    | [_], _ => simp [Inv]
    | a :: b :: rest, hne => exact absurd rfl (hne a b rest)

/-- Under the invariant the fast path returns exactly the spec. -/
theorem fast_eq_spec (n : Nat) (posts : List Post) (h : Inv posts) :
    fast n posts = spec n posts := by
  unfold fast spec
  congr 1
  symm
  apply List.Perm.eq_of_pairwise (le := fun a b => before a b = true)
  · intro a b ha hb hab hba
    have ha' : a ∈ posts := (List.mergeSort_perm posts before).subset ha
    have hb' : b ∈ posts := List.mem_reverse.mp hb
    obtain ⟨i, hi, rfl⟩ := List.getElem_of_mem ha'
    obtain ⟨j, hj, rfl⟩ := List.getElem_of_mem hb'
    have hp := List.pairwise_iff_getElem.mp h
    rcases Nat.lt_trichotomy i j with hij | rfl | hij
    · have := hp i j hi hj hij; simp [before, lt] at *; omega
    · rfl
    · have := hp j i hj hi hij; simp [before, lt] at *; omega
  · exact List.pairwise_mergeSort
      (fun a b c h₁ h₂ => by simp [before, lt] at *; omega)
      (fun a b => by simp [before, lt]; omega) posts
  · exact List.pairwise_reverse.mpr (h.imp fun hab => by simp [before, lt] at *; omega)
  · exact (List.mergeSort_perm posts before).trans (List.reverse_perm posts).symm

/-- The spec never returns more than `n` posts. -/
theorem spec_length_le (n : Nat) (posts : List Post) : (spec n posts).length ≤ n := by
  simp [spec]; omega

end Feed
