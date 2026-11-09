### Hey, I'm Darshan

[![Portfolio](https://img.shields.io/badge/Portfolio-darshan--05032003.github.io-000?style=flat&logo=githubpages)](https://darshan-05032003.github.io/portfolio-v2/)

I build Android apps in Kotlin and Flutter, and the Spring Boot services behind them. My portfolio, with screenshots and the engineering decisions behind each project, is [here](https://darshan-05032003.github.io/portfolio-v2/).

Most of my recent work is about software that has to stay correct under pressure: payments that a retry can't charge twice, stock that can't be oversold when twenty people buy at once, and a ledger the database itself won't let you edit. Every project below is test-first and checked against the failure it's meant to prevent.

I'm open to Android, Flutter and backend roles, and to freelance work. You can reach me by email [here](mailto:sonawanedarshan35@gmail.com).

#### Building

- **[PayFlow](https://github.com/Darshan-05032003/PayFlow)** [![GitHub stars](https://img.shields.io/github/stars/Darshan-05032003/PayFlow?style=flat&color=gold)](https://github.com/Darshan-05032003/PayFlow) - Android UPI payments app (Kotlin, Compose). Compare-and-set status updates and idempotency keys mean a retried payment can't settle twice. Includes QR pay and receive, collect requests, AutoPay mandates and Keystore-encrypted storage.
- **[SplitSmart](https://github.com/Darshan-05032003/SplitSmart)** [![GitHub stars](https://img.shields.io/github/stars/Darshan-05032003/SplitSmart?style=flat&color=gold)](https://github.com/Darshan-05032003/SplitSmart) - Photograph a bill and split it to the exact paisa. On-device ML Kit OCR plus Gemini extraction, with the LLM output validated as untrusted input; UPI settle-up links and QR codes.
- **[CheckoutKit](https://github.com/Darshan-05032003/CheckoutKit)** [![GitHub stars](https://img.shields.io/github/stars/Darshan-05032003/CheckoutKit?style=flat&color=gold)](https://github.com/Darshan-05032003/CheckoutKit) - Kotlin Multiplatform payment SDK: a Compose payment sheet on top of a pure state machine that rejects illegal transitions. Published on JitPack and used by PayFlow.
- **[Fin_Pay](https://github.com/Darshan-05032003/Fin_Pay)** [![GitHub stars](https://img.shields.io/github/stars/Darshan-05032003/Fin_Pay?style=flat&color=gold)](https://github.com/Darshan-05032003/Fin_Pay) - Offline-first Flutter fintech app with BLoC, clean architecture, a sqflite ledger, golden tests and GitHub Actions CI.
- **[core-banking-ledger](https://github.com/Darshan-05032003/core-banking-ledger)** [![GitHub stars](https://img.shields.io/github/stars/Darshan-05032003/core-banking-ledger?style=flat&color=gold)](https://github.com/Darshan-05032003/core-banking-ledger) - Double-entry banking ledger in Spring Boot. PostgreSQL triggers make it append-only, transfers go through maker-checker approval, and Kafka events are published through a transactional outbox. Tested with Testcontainers.
- **[ecommerce-backend](https://github.com/Darshan-05032003/ecommerce-backend)** [![GitHub stars](https://img.shields.io/github/stars/Darshan-05032003/ecommerce-backend?style=flat&color=gold)](https://github.com/Darshan-05032003/ecommerce-backend) - Shop backend in Spring Boot that can't oversell: a conditional stock update, idempotent checkout and rotating refresh tokens. One test runs 20 concurrent buyers against MySQL in Testcontainers.
- **[transaction-reconciliation-batch](https://github.com/Darshan-05032003/transaction-reconciliation-batch)** [![GitHub stars](https://img.shields.io/github/stars/Darshan-05032003/transaction-reconciliation-batch?style=flat&color=gold)](https://github.com/Darshan-05032003/transaction-reconciliation-batch) - Spring Batch job that matches a bank statement against the ledger and classifies every mismatch. Partitioned and restartable, with duplicate-file detection.
- **[portfolio-v2](https://github.com/Darshan-05032003/portfolio-v2)** [![GitHub stars](https://img.shields.io/github/stars/Darshan-05032003/portfolio-v2?style=flat&color=gold)](https://github.com/Darshan-05032003/portfolio-v2) - My portfolio, hand-written in HTML, CSS and JavaScript. It also has browser simulations of overselling, a double charge and an append-only ledger.

#### Also built

- **[Learning_dashboard_app](https://github.com/Darshan-05032003/Learning_dashboard_app)** - Flutter course dashboard with feature-first clean architecture and BLoC.
- **[Investor_Deal_App](https://github.com/Darshan-05032003/Investor_Deal_App)** - Flutter deal browser with filters and search, built with BLoC.
- **[Portfolio](https://github.com/Darshan-05032003/Portfolio)** - An F1-themed version of my portfolio: a procedural 3D race car in three.js that brakes and corners as you scroll. Live [here](https://darshan-portfolio-6vo.pages.dev/).
