# Infrastructure reference

The Kubernetes manifests demonstrate a hardened API runtime:

- non-root user;
- read-only root filesystem;
- all Linux capabilities dropped;
- seccomp `RuntimeDefault`;
- no service-account token;
- memory-backed `/tmp`;
- readiness and liveness probes;
- CPU and memory requests/limits;
- restricted ingress and DNS-only egress.

Replace the placeholder container image and create the `credit-risk-api` secret through an
approved secret-management process. Do not commit a Secret manifest with plaintext values.
