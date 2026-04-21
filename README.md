# TestForge - Mutation Testing Framework

<div align="center">

![TestForge Logo](https://img.shields.io/badge/TestForge-Mutation%20Testing-blue)
[![CI](https://github.com/moggan1337/TestForge/actions/workflows/ci.yml/badge.svg)](https://github.com/moggan1337/TestForge/actions/workflows/ci.yml)
[![npm version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/moggan1337/TestForge)

</div>

> **Find the bugs your tests don't catch.** TestForge uses mutation testing to measure and improve your test suite quality.

## 🎬 Demo

![TestForge Demo](demo.gif)

*Mutation testing in action - catching weak tests*

## ✨ Features

- **Automatic mutation generation** - Creates meaningful code mutations
- **Intelligent mutation operators** - Industry-standard + custom operators
- **Parallel execution** - Fast mutation testing with worker threads
- **Coverage integration** - Prioritize mutations by code coverage
- **CI/CD integration** - Fail builds on mutation score thresholds

## 🚀 Quick Start

```bash
npm install -g @moggan1337/testforge
testforge init
testforge run
```

## 🧪 Mutation Testing Demo

### Before & After Mutation Testing

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        TESTFORGE MUTATION ANALYSIS                               │
│                        Project: user-auth-service                               │
│                        Timestamp: 2024-04-21 14:32:18                            │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Mutation Example 1: Boundary Condition

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  MUTATION #001: BOUNDARY CHANGE                                                 │
│  File: src/utils/validators.ts                                                  │
│  Operator: BCR (Boundary Conditionals)                                          │
└─────────────────────────────────────────────────────────────────────────────────┘

  ORIGINAL CODE:
  ┌─────────────────────────────────────────────────────────────────────────────┐
  │  export function validateAge(age: number): boolean {                        │
  │    if (age >= 18) {           ←── TEST PASSED ✓ (original)                 │
  │      return true;                                                             │
  │    }                                                                         │
  │    return false;                                                             │
  │  }                                                                           │
  └─────────────────────────────────────────────────────────────────────────────┘

  MUTATION APPLIED (age >= 18 → age > 18):
  ┌─────────────────────────────────────────────────────────────────────────────┐
  │  export function validateAge(age: number): boolean {                        │
  │    if (age > 18) {            ←── MUTATED (age >= 18 → age > 18)          │
  │      return true;                                                             │
  │    }                                                                         │
  │    return false;                                                             │
  │  }                                                                           │
  └─────────────────────────────────────────────────────────────────────────────┘

  RESULT: ❌ SURVIVED (Test suite did NOT catch this bug!)
  
  ┌─────────────────────────────────────────────────────────────────────────────┐
  │  ⚠️  WARNING: Your tests have a gap!                                       │
  │                                                                             │
  │  Test 'validateAge accepts exactly 18' exists but doesn't fail.            │
  │  Add test case: expect(validateAge(18)).toBe(true)                          │
  └─────────────────────────────────────────────────────────────────────────────┘
```

### Mutation Example 2: Negated Condition

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  MUTATION #002: NEGATED CONDITION                                               │
│  File: src/services/payment.ts                                                 │
│  Operator: COND (Conditional Negation)                                         │
└─────────────────────────────────────────────────────────────────────────────────┘

  ORIGINAL CODE:
  ┌─────────────────────────────────────────────────────────────────────────────┐
  │  if (user.isActive && user.hasPaymentMethod) {         ←── TEST PASSED ✓    │
  │    processPayment();                                                          │
  │  }                                                                           │
  └─────────────────────────────────────────────────────────────────────────────┘

  MUTATION APPLIED (&& → ||):
  ┌─────────────────────────────────────────────────────────────────────────────┐
  │  if (user.isActive || user.hasPaymentMethod) {        ←── MUTATED           │
  │    processPayment();                                                          │
  │  }                                                                           │
  └─────────────────────────────────────────────────────────────────────────────┘

  RESULT: ❌ SURVIVED (Test suite did NOT catch this bug!)

  ┌─────────────────────────────────────────────────────────────────────────────┐
  │  💀 CRITICAL: A user without payment method could have payment processed!   │
  │                                                                             │
  │  Your tests need explicit verification of BOTH conditions being required.   │
  └─────────────────────────────────────────────────────────────────────────────┘
```

### Mutation Example 3: Return Value Swap

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  MUTATION #003: RETURN VALUE MODIFICATION                                       │
│  File: src/utils/auth.ts                                                        │
│  Operator: RVR (Return Value Replacement)                                      │
└─────────────────────────────────────────────────────────────────────────────────┘

  ORIGINAL CODE:
  ┌─────────────────────────────────────────────────────────────────────────────┐
  │  export function isAuthenticated(token: string): boolean {                  │
  │    return verifyToken(token) !== null;    ←── TEST PASSED ✓                 │
  │  }                                                                           │
  └─────────────────────────────────────────────────────────────────────────────┘

  MUTATION APPLIED (true → false):
  ┌─────────────────────────────────────────────────────────────────────────────┐
  │  export function isAuthenticated(token: string): boolean {                  │
  │    return false;                         ←── MUTATED                        │
  │  }                                                                           │
  └─────────────────────────────────────────────────────────────────────────────┘

  RESULT: ✓ KILLED (Test caught this mutation!)

  ┌─────────────────────────────────────────────────────────────────────────────┐
  │  ✓ Test 'isAuthenticated rejects invalid tokens' caught the mutation.       │
  │  ✓ Mutation score improved by 0.5%                                          │
  └─────────────────────────────────────────────────────────────────────────────┘
```

### TestForge Report Summary

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           MUTATION TESTING REPORT                                │
│                           ════════════════════════                               │
│                           Generated: 2024-04-21 14:35:22                        │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  SUMMARY                                                                         │
│  ───────                                                                         │
│  Files analyzed:          47                                                    │
│  Lines of code:           2,341                                                 │
│  Mutations generated:     156                                                    │
│  ─────────────────────────────────────                                          │
│  ✓ Killed:               134  (85.9%)                                          │
│  ❌ Survived:             18  (11.5%)   ⚠️ NEEDS ATTENTION                      │
│  ⏱️  Timeout:              4  (2.6%)                                            │
│                                                                                  │
│  MUTATION SCORE:  85.9%  (Target: > 80%)  ✓ PASSED                              │
│                                                                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│  CRITICAL SURVIVED MUTATIONS (FIX THESE FIRST)                                  │
│  ────────────────────────────────────────────                                   │
│                                                                                  │
│  🔴 src/services/payment.ts:47                                                  │
│     user.isActive && user.hasPaymentMethod → user.isActive || ...               │
│     → Allows payments without payment method                                    │
│                                                                                  │
│  🔴 src/utils/validators.ts:23                                                  │
│     age >= 18 → age > 18                                                        │
│     → 18-year-olds incorrectly rejected                                         │
│                                                                                  │
│  🔴 src/api/orders.ts:89                                                        │
│     total > 0 → total >= 0                                                      │
│     → Free orders not properly handled                                          │
│                                                                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│  WARNING SURVIVED MUTATIONS                                                      │
│  ─────────────────────────                                                      │
│                                                                                  │
│  🟡 src/utils/format.ts:12 - String concatenation mutation survived            │
│  🟡 src/services/email.ts:34 - Null check removed, test covers implicitly      │
│  🟡 src/api/users.ts:56 - Empty array check mutated to length === 0            │
│                                                                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│  COVERAGE VS MUTATION ANALYSIS                                                  │
│  ───────────────────────────────                                                │
│                                                                                  │
│  Line Coverage:     92% (looks good!)                                           │
│  Branch Coverage:   78% (decent)                                                │
│  Mutation Score:    86% (reality check!)                                        │
│                                                                                  │
│  💡 INSIGHT: High line coverage doesn't mean your tests are thorough!           │
│     Mutation testing reveals that 14% of your logic has weak test coverage.    │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Mutation Operators Applied

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        MUTATION OPERATORS USED                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  CONDITIONAL NEGATION (COND)              ████████████████████░░░  45 mutants   │
│  BOUNDARY CHANGES (BCR)                    ████████████░░░░░░░░░░░░░  28 mutants   │
│  RETURN VALUE REPLACEMENT (RVR)            ████████░░░░░░░░░░░░░░░░  19 mutants   │
│  ARITHMETIC REPLACEMENT (AOR)              █████░░░░░░░░░░░░░░░░░░░  12 mutants   │
│  LOGICAL REPLACEMENT (LOR)                 ████░░░░░░░░░░░░░░░░░░░░   9 mutants    │
│  METHOD CALL DELETION (MCD)                ███░░░░░░░░░░░░░░░░░░░░   7 mutants    │
│  VOID METHOD CALLS (VMC)                   ██░░░░░░░░░░░░░░░░░░░░░   5 mutants    │
│  DECREMENT/INCREMENT (DOI)                 ██░░░░░░░░░░░░░░░░░░░░░   5 mutants    │
│  REMOVE DEFAULTS (RDD)                     █░░░░░░░░░░░░░░░░░░░░░░   3 mutants    │
│  CONSTANT REPLACEMENT (CRP)                █░░░░░░░░░░░░░░░░░░░░░░   3 mutants    │
│                                                                                  │
│  Other operators:                                       20 mutants              │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### CI/CD Integration

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         GITHUB ACTIONS INTEGRATION                              │
└─────────────────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────────────────┐
  │  # .github/workflows/mutation-tests.yml                                     │
  │  name: Mutation Testing                                                     │
  │                                                                             │
  │  on: [push, pull_request]                                                   │
  │                                                                             │
  │  jobs:                                                                      │
  │    mutation-test:                                                           │
  │      runs-on: ubuntu-latest                                                 │
  │      steps:                                                                 │
  │        - uses: actions/checkout@v4                                          │
  │        - uses: actions/setup-node@v4                                        │
  │        - run: npm ci                                                        │
  │        - name: Run TestForge                                                │
  │          run: npx testforge run --threshold 80                             │
  └─────────────────────────────────────────────────────────────────────────────┘

  RUNNING WORKFLOW...
  
  ✓ Checked out code
  ✓ Installed dependencies
  ✓ Running mutation tests...
  
  ████████████████████████ 100%
  
  Mutation Score: 85.9% (Threshold: 80%)
  
  ✓ BUILD PASSED
  
  📊 Report: https://testforge.dev/reports/abc123
```

## 🛠️ Installation

```bash
# Global installation
npm install -g @moggan1337/testforge

# Project installation
npm install --save-dev @moggan1337/testforge
```

## 📖 Usage

```bash
# Initialize TestForge configuration
testforge init

# Run mutation tests
testforge run

# Run with coverage
testforge run --coverage

# Set minimum mutation score threshold
testforge run --threshold 85

# Watch mode
testforge watch

# Generate HTML report
testforge report --format html --output ./reports/mutations.html
```

## 📊 Supported Test Frameworks

| Framework | Support |
|-----------|---------|
| Jest | ✅ Full |
| Vitest | ✅ Full |
| Mocha | ✅ Full |
| pytest | ✅ Full |
| JUnit | ✅ Full |

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

MIT © 2024 moggan1337
