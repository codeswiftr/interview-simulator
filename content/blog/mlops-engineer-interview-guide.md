---
title: "MLOps Engineer Interview Guide"
description: "Technical interview preparation for MLOps and ML infrastructure engineering roles: model serving, feature stores, training pipelines, model monitoring, and what companies like Databricks, Weights & Biases, Hugging Face, and ML-driven product companies expect from MLOps engineers."
date: "2026-03-19"
category: "Specialty Engineering Roles"
---

MLOps engineering sits at the intersection of machine learning and production infrastructure. The role exists because the gap between a data scientist's notebook and a reliable production system is enormous — and that gap costs companies real money when models silently degrade, pipelines fail, or inference latency spikes under load. If you are preparing for an MLOps interview, you need to demonstrate that you understand both sides: the ML concepts and the infrastructure discipline required to make them work at scale.

## What MLOps Actually Covers

The core problem is operationalizing models. A model that performs well in a notebook is not a product. MLOps engineers build and own:

- **Training pipelines** — reproducible, versioned workflows for data ingestion, preprocessing, training, and evaluation
- **Model serving infrastructure** — APIs, latency SLOs, hardware utilization, scaling policies
- **Feature engineering at scale** — consistent feature computation across training and serving
- **Model monitoring** — detecting when models stop performing as expected
- **Data versioning** — tracking what data was used to train each model version

Interviewers will probe whether you understand why each of these areas exists, not just how to operate the tools.

## Feature Stores

Feature stores solve two concrete problems: **training-serving skew** and **feature reuse across teams**.

Training-serving skew happens when the feature logic used during training differs from the logic used at inference time — different code paths, different data sources, or time-leakage bugs. A feature store enforces a single definition computed once and used everywhere.

**Architecture:**
- **Offline store** — batch storage (typically a data warehouse or data lake: Snowflake, BigQuery, S3 + Parquet) used during training and batch inference
- **Online store** — low-latency key-value storage (Redis, DynamoDB, Cassandra) used during real-time serving
- **Feature registry** — metadata catalog of feature definitions, owners, and lineage

**The main platforms:**
- **Feast** — open-source, composable, widely used, you bring your own infrastructure
- **Tecton** — managed, strong on real-time features, expensive, used heavily at fintech companies
- **Hopsworks** — open-source with a managed offering, includes a feature store and a model registry

Be ready to explain the difference between point-in-time correct feature joins (critical to avoid target leakage) and naive joins. Most candidates miss this.

## Model Serving Infrastructure

Serving is where infrastructure discipline matters most. Key dimensions:

**Protocol:**
- **REST** — easier to integrate, higher overhead per request
- **gRPC** — lower latency, binary protocol, better for high-throughput internal services

**Batching inference:** Grouping requests into mini-batches before sending to the model increases GPU utilization significantly. NVIDIA Triton Inference Server handles dynamic batching natively and is the standard for GPU serving at scale.

**Model versioning and canary deployments:** Models are software artifacts. You need the same deployment rigor applied to code: blue/green and canary strategies let you roll out a new model version to a percentage of traffic, compare metrics against the incumbent, and roll back safely. Tools like Seldon Core and KServe (formerly KFServing) implement this on Kubernetes.

**NVIDIA Triton:** The production-grade GPU inference server. Supports TensorRT, ONNX, PyTorch TorchScript, and TensorFlow SavedModel backends. Interviewers at companies with heavy GPU workloads will expect you to know about model ensembles, the Triton model repository layout, and concurrent model execution.

## Training Pipelines

Training pipelines encode the workflow of producing a model as a DAG of reproducible steps. The key properties are: versioned inputs and outputs, parameterized steps, and support for partial re-execution when only some steps change.

**Orchestration frameworks:**
- **Kubeflow Pipelines (KFP)** — Kubernetes-native, containerized steps, strong on reproducibility, steep setup overhead
- **MLflow Pipelines (Projects)** — lighter weight, tied to the MLflow ecosystem
- **ZenML** — stack-agnostic, good developer experience, growing adoption

**Experiment tracking** is closely related. Every training run should log hyperparameters, metrics, artifacts, and the git commit. The main tools:
- **MLflow Tracking** — open-source, self-hostable, SQL-backed
- **Weights & Biases (W&B)** — managed, excellent UI, strong on sweep (hyperparameter search) automation
- **Neptune.ai** — similar to W&B, strong metadata storage model

Interviewers will ask you about reproducibility: can you recreate any model from six months ago exactly? Your answer needs to cover data versioning (DVC, Delta Lake, or a data catalog with snapshot support), code versioning (git), and artifact versioning (MLflow model registry or a blob store with immutable object naming).

## Model Monitoring

Models degrade in production for two distinct reasons:

**Data drift** — the statistical distribution of incoming features changes from the training distribution. Tests:
- Kolmogorov-Smirnov (KS) test for continuous features
- Population Stability Index (PSI) — commonly used in credit risk MLOps
- Chi-squared test for categorical features

**Concept drift** — the relationship between features and the target changes, even if input distributions look similar. This is harder to detect without ground truth labels.

**Prediction monitoring** — track output distribution shifts even when ground truth is unavailable. Sudden spikes in high-confidence predictions or collapse in prediction diversity are early warning signals.

**Ground truth logging** — for systems where labels arrive with a delay (e.g., fraud detection, churn), build pipelines to ingest delayed labels, compute retrospective performance metrics, and trigger retraining jobs when performance drops below a threshold.

Tools: Evidently AI (open-source), WhyLabs, Arize, Fiddler.

## Infrastructure: Kubernetes, GPUs, and Distributed Training

MLOps engineers own the infrastructure layer, which means Kubernetes fluency is required at most serious companies.

**GPU scheduling:** Kubernetes does not schedule GPUs natively at a fine-grained level. You need the NVIDIA device plugin, and at scale, tools like NVIDIA GPU Operator and time-slicing configurations. MIG (Multi-Instance GPU) partitioning is relevant for serving workloads where full GPU utilization per request is wasteful.

**Distributed training:**
- **Horovod** — ring-allreduce, framework-agnostic, widely deployed
- **PyTorch DDP (DistributedDataParallel)** — the standard for PyTorch, NCCL backend for GPU-to-GPU communication
- **DeepSpeed** — Microsoft's library, essential for large model training with ZeRO optimizer stages

**Ray** — a distributed Python framework that unifies training, hyperparameter tuning (Ray Tune), serving (Ray Serve), and data processing. It has become the de facto standard for ML platform teams that want a single abstraction layer across heterogeneous workloads.

## Who Hires MLOps Engineers and What the Interview Looks Like

**Companies actively hiring:**
- **Databricks** — heavy MLflow and Spark ecosystem, expect questions on Delta Lake, Unity Catalog, and MLflow Model Serving
- **Weights & Biases** — product is an MLOps tool, expect deep questions on experiment tracking internals, artifact lineage, and SDK design
- **Hugging Face** — model hub infrastructure, inference endpoints, distributed training at scale
- **Netflix, Spotify, Uber, DoorDash** — large internal ML platforms, emphasis on reliability, feature stores, and serving infrastructure
- **Fintech companies** — model governance, regulatory requirements for model explainability and audit trails

**The interview process typically includes:**

- **System design round** — design a feature store, a real-time model serving system, or a training pipeline. Show that you reason about consistency, latency, fault tolerance, and cost tradeoffs.
- **Coding round** — Python is required, often Pandas and SQL for data manipulation, sometimes a pipeline design exercise
- **Infrastructure round** — Kubernetes, Docker, CI/CD for ML, sometimes Terraform or Helm
- **ML fundamentals check** — you should understand what the model does well enough to reason about its failure modes. Pure infrastructure candidates without ML depth rarely pass.

The differentiator in MLOps interviews is operational thinking: not just "how do you train a model" but "what happens when the model starts performing badly at 2am, and how do you catch it before users notice."
