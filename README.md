# drift-check

> Utility that diffs live infrastructure state against Terraform configs and reports configuration drift.

---

## Installation

```bash
pip install drift-check
```

Or install from source:

```bash
git clone https://github.com/yourorg/drift-check.git && cd drift-check && pip install .
```

---

## Usage

Point `drift-check` at your Terraform working directory and let it compare live infrastructure state against your configuration files.

```bash
# Check for drift in the current directory
drift-check --dir ./infra

# Target a specific Terraform state file
drift-check --dir ./infra --state terraform.tfstate

# Output results as JSON
drift-check --dir ./infra --output json
```

**Example output:**

```
[DRIFT DETECTED] aws_instance.web
  - instance_type: expected "t3.micro", got "t3.small"

[DRIFT DETECTED] aws_s3_bucket.assets
  - versioning.enabled: expected true, got false

[OK] aws_security_group.default
Summary: 2 drifted resources, 1 clean
```

---

## Configuration

Optional config file (`.drift-check.yml`) in your project root:

```yaml
ignore:
  - aws_instance.*.tags
output: table   # table | json | quiet
fail_on_drift: true
```

---

## Contributing

Pull requests are welcome. Please open an issue first to discuss proposed changes.

---

## License

This project is licensed under the [MIT License](LICENSE).