# Dialogue state and multi-turn continuation

The supplied application loads a dialogue state using `sender_id`, runs one turn, and saves the updated state after processing.

The state includes items such as:

- current workflow and step;
- collected fields such as order number or refund reason;
- focused order/product context;
- session/turn information needed for continuation.

The repository serializes the state as JSON text and stores it in a text field. It is therefore JSON-serialized content in MySQL-backed storage, not a native MySQL `JSON` column.

## Example continuation

During a refund dialogue, an order number may already be available while the workflow is waiting for a refund reason. When the next user message arrives, the saved state allows the remaining step to continue without restarting the flow.

## Limits

This portfolio does not claim that `sender_id` is an authentication mechanism, nor does it claim production-grade concurrency or session security. It documents the behavior supported by the supplied source and owner-run demonstration.
