# Logic map

How an order becomes a delivery quote.
Rule: if you change a step, update this file in the same commit.
`tests/test_logic_map.py` checks that every `Module:` line points to a real module.
The Russian mirror is `docs/logic-map.ru.md`; this file is the source of truth.

## Steps

### 1. Read the order

Decides: items, their total weight in grams, the order total in tenge, express or not.
Fails: a malformed order is rejected with a message.
Module: `quote/__init__`

### 2. Pick the warehouse

Decides: which warehouse ships.
A warehouse that has every item wins; among those, the nearest; equal distance, the lower id.
No warehouse has everything: the one with the most items; equal, the lower id.
Module: `quote/warehouse`

### 3. Price the delivery

Decides: what the customer pays for delivery.
Delivery is free for orders from 20 000 ₸.
Standard delivery is 1 000 ₸ plus 200 ₸ for each kg above 5 kg.
Express costs twice the standard price.
Fails: never; the price is a whole number of tenge.
Module: `quote/price`

### 4. Send the quote

Decides: nothing; the quote goes to the customer by email.
Module: `quote/__init__`

## Known gaps

Open findings are in `docs/PLAN.md`.
