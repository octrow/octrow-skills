/-! Executable model of `feed.py`: the reference the Python code is checked against. -/
namespace Feed

structure Post where
  id : Nat
  createdAt : Nat
  authorId : Nat
deriving Repr, DecidableEq

/-- `a` is strictly older than `b` in `(created_at, id)` order. -/
def lt (a b : Post) : Bool :=
  a.createdAt < b.createdAt || (a.createdAt == b.createdAt && a.id < b.id)

/-- `a` may stand before `b` in the feed: newer or same key. -/
def before (a b : Post) : Bool := !lt a b

/-- Spec: `sorted(posts, key=(created_at, id), reverse=True)[:n]`. -/
def spec (n : Nat) (posts : List Post) : List Post :=
  (posts.mergeSort before).take n

/-- Fast path: `posts[-n:][::-1]`. Right only when the invariant holds. -/
def fast (n : Nat) (posts : List Post) : List Post :=
  posts.reverse.take n

/-- Invariant: posts are stored in strictly increasing `(created_at, id)` order. -/
def Inv (posts : List Post) : Prop :=
  posts.Pairwise (fun a b => lt a b = true)

/-- Runtime check of `Inv`, one pass over neighbours. Mirrors `is_ordered` in `feed.py`. -/
def checkInv : List Post → Bool
  | a :: b :: rest => lt a b && checkInv (b :: rest)
  | _ => true

end Feed
