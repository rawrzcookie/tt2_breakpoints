# Tap Titans 2 - Event Breakpoints

Automatically performs the following actions:
1. Query Gamehive's Breakpoints Endpoint at `https://tt2.gamehivegames.com/holiday_event/breakpoint`
2. Update the [`breakpoints.csv`](https://github.com/rawrzcookie/tt2_breakpoints/blob/main/breakpoints.csv) file
   1. Appends new row if a new event goes live
   2. Otherwise, updates data for current event row
3. Posts message to Discord via a Discord Webhook
   1. Posts a new message if a new event goes live
   2. Otherwise, edits the message with new data

Preview in my [Discord Server](https://discord.gg/vNv7ZfCFsX)

