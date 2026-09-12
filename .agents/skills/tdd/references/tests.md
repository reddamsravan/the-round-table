# Good and Bad Tests

## Good Tests

**Integration-style**: Test through real interfaces, not mocks of internal parts.

```typescript
// GOOD: Tests observable behavior
test("user can checkout with valid cart", async () => {
  const cart = createCart();
  cart.add(product);
  const result = await checkout(cart, paymentMethod);
  expect(result.status).toBe("confirmed");
});
```

Characteristics:

- Tests behavior the caller cares about
- Uses the public API only
- Survives internal refactors
- Describes WHAT, not HOW
- One logical assertion per test
- Test name reads as a specification sentence

## Bad Tests

**Implementation-detail tests**: Coupled to internal structure.

```typescript
// BAD: Tests implementation details
test("checkout calls paymentService.process", async () => {
  const mockPayment = jest.mock(paymentService);
  await checkout(cart, payment);
  expect(mockPayment.process).toHaveBeenCalledWith(cart.total);
});
```

Red flags:

- Mocking internal collaborators
- Testing private methods
- Asserting on call counts or invocation order of internal functions
- Test name describes HOW code works, not WHAT it does
- Test breaks when you rename an internal variable or extract a helper

## Test Naming

Name tests as user-facing specifications:

```
"user can checkout with valid cart"          // GOOD
"checkout calls paymentService.process"     // BAD
"returns 200 when cart is valid"            // BAD — describes HTTP plumbing
"user receives order confirmation on checkout" // GOOD
```

A test name MUST state: who does what, under what condition, and with what observable result.

## One Logical Assertion

Each test covers one behavior. Multiple assertions are acceptable when they together verify one logical outcome.

```typescript
// GOOD: Two assertions, one logical outcome
expect(result.status).toBe("confirmed");
expect(result.orderId).toBeDefined();

// BAD: Two unrelated behaviors in one test
expect(result.status).toBe("confirmed");
expect(emailQueue.length).toBe(1); // separate behavior — write a separate test
```
