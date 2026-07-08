# Pass 04 - Pair Commands to Results

This is the first really useful mining pass.

A likely command is something like:
```
<player> says (to Floyd), "<command>"
<player> says (to CF), "<command>"
<player> says (to ClubFloyd), "<command>"
```

Example commands common in text adventures and interactive fiction (not an exhaustive list):
```
look
look at
look in
look through
open / close
take / drop
put X in Y
put X on Y
unlock X with Y
ask/tell/show/give
push / pull
break
listen
smell
eat / drink
inventory
go directions
parser failures and synonym retries
```

The gold isn't just in the ask: the result, or the failure resolution pattern, is very valuable to understand:

```
> look window
failure
> examine window
partial success
> open window
state change
> look through window
rich result
```

