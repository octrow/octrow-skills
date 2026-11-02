import Spec.Feed.Model
/-! Oracle for differential tests. Long-lived: one request per line.
In:  `n id created_at author_id id created_at author_id ...`
Out: `spec n posts` in the same triple format (whole posts, as the theorems compare them), or `error: <reason>`. -/
open Feed

def parsePosts : List Nat → Option (List Post)
  | [] => some []
  | i :: c :: a :: rest => (⟨i, c, a⟩ :: ·) <$> parsePosts rest
  | _ => none

def answer (line : String) : String :=
  let words := ((line.replace "\n" "").splitOn " ").filter (· ≠ "")
  match words.mapM String.toNat? with
  | some (n :: rest) =>
    match parsePosts rest with
    | some posts => " ".intercalate ((spec n posts).map fun p => s!"{p.id} {p.createdAt} {p.authorId}")
    | none => "error: post fields must come in triples"
  | _ => "error: expected natural numbers"

partial def loop (stdin : IO.FS.Stream) (stdout : IO.FS.Stream) : IO Unit := do
  let line ← stdin.getLine
  if line.isEmpty then return
  stdout.putStrLn (answer line)
  stdout.flush
  loop stdin stdout

def main : IO Unit := do
  loop (← IO.getStdin) (← IO.getStdout)
