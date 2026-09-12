# When and How to Mock

## Mock at System Boundaries Only

Mock only what the project does not control:

- External APIs (payment, email, SMS, third-party services)
- Time and randomness (`Date.now`, `Math.random`, `crypto.randomUUID`)
- File system, when unavailable in the test environment
- Network calls to services outside the test process

Prefer a real test database over mocking the database layer. A test DB catches SQL errors, schema mismatches, and constraint violations that a mock never will.

Do not mock:

- Your own classes or modules
- Internal collaborators
- Anything the project owns and controls

## Designing for Mockability

At system boundaries, design interfaces that inject dependencies rather than construct them internally.

**1. Use dependency injection**

Pass external dependencies in rather than creating them inside the function:

```typescript
// Easy to mock — dependency injected
function processPayment(order, paymentClient) {
  return paymentClient.charge(order.total);
}

// Hard to mock — dependency constructed internally
function processPayment(order) {
  const client = new StripeClient(process.env.STRIPE_KEY);
  return client.charge(order.total);
}
```

**2. Use SDK-style interfaces**

Define a narrow interface for the external dependency. Mock the interface, not the full SDK:

```typescript
// Define a narrow interface
interface PaymentClient {
  charge(amount: number): Promise<{ id: string }>;
}

// Mock the interface in tests — not the full Stripe SDK
const fakePaymentClient: PaymentClient = {
  charge: async (amount) => ({ id: "test-charge-id" }),
};
```

This decouples tests from the third-party SDK's internal shape.

## Decision Table

| Dependency | Strategy |
| :--- | :--- |
| External API (payment, email) | Mock the interface at the boundary |
| Database | Prefer test DB; mock only when unavailable |
| Time / `Date.now` | Mock with a fixed timestamp |
| `Math.random` / randomness | Mock with a fixed seed or stub |
| File system | Use temp directory when possible; mock when unavailable |
| Internal module / class | Never mock — test through it |
| Internal helper function | Never mock — test through the public interface |
