# Weibo chat send pacing

This flow is for `https://api.weibo.com/chat/#/chat?...` pages only. It is not a general web automation risk model.

Current conservative pacing:

- Start each target at least 20 seconds after the previous target starts.
- After opening the chat URL, wait 5-7 seconds before interacting.
- Type messages gradually instead of filling the whole textarea at once.
- After typing, wait 1-5 seconds before sending.
- After sending, wait 5-10 seconds before moving to the next target.
- In batch mode, this keeps throughput at no more than 3 targets per minute.

Observed baseline:

- Fast repeated send + page refresh on the same Weibo chat URL can trigger a temporary Chrome error page:
  - `该网页无法正常运作`
  - `如果问题仍然存在，请与网站所有者联系。`
  - `HTTP ERROR 418`
- The observed temporary block recovered after roughly 3 minutes.

Implementation notes:

- The pacing lives in `src/policies/weibo_chat_policy.py`.
- `HumanActor` only performs slower typing/clicking mechanics.
- `WeiboChatPage` only knows page selectors and page interaction.
- `WeiboAdapter` applies the Weibo chat policy for this specific scenario.
