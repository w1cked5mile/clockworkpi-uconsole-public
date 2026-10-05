---
id: channel-hopping
term: Channel hopping
tooltip: Retuning one radio across channels in turn, because it can only listen to one at a time.
good_bad: "Fancy's Kismet config hops 5 times a second. Faster finds more networks; slower hears more from each."
try_this: "Compare the network count from a hopping survey with one locked to channel 6."
learn_more: "#/learn/m/M7"
---

A single Wi-Fi radio hears one channel at a time. Kismet hops through the channel list, dwelling
briefly on each, so it sees most networks but misses frames sent while it is elsewhere. Don't
change the hop settings mid-survey, or two halves of the data can't be compared.
