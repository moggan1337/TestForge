"""
CI/CD pipeline integration for mutation testing.

Supports GitHub Actions, GitLab CI, Jenkins, and more.
"""

from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import json
import yaml


class CIPlatform(Enum):
    """Supported CI/CD platforms."""
    GITHUB_ACTIONS = "github_actions"
    GITLAB_CI = "gitlab_ci"
    JENKINS = "jenkins"
    CIRCLE_CI = "circle_ci"
    TRAVIS_CI = "travis_ci"
    AZURE_DEVOPS = "azure_devops"


@dataclass
class CIConfig:
    """Configuration for CI/CD integration."""
    platform: CIPlatform = CIPlatform.GITHUB_ACTIONS
    threshold: float = 80.0  # Minimum mutation score to pass
    parallel_jobs: int = 4
    timeout: int = 3600  # seconds
    fail_on_threshold: bool = True
    upload_reports: bool = True
    report_format: str = "html"  # html, json, markdown
    comment_on_pr: bool = True
    notifications_enabled: bool = True


@dataclass
class PipelineStep:
    """A step in the CI/CD pipeline."""
    name: str
    command: str
    condition: Optional[str] = None
    continue_on_error: bool = False


class CIPipeline:
    """
    CI/CD pipeline integration for mutation testing.
    
    Generates pipeline configurations and provides utilities
    for integrating mutation testing into CI/CD workflows.
    """
    
    def __init__(self, config: Optional[CIConfig] = None):
        self.config = config or CIConfig()
    
    def generate_github_actions(
        self,
        project_root: Path,
        output_path: Optional[Path] = None,
    ) -> str:
        """
        Generate GitHub Actions workflow for mutation testing.
        
        Args:
            project_root: Path to project root
            output_path: Optional path to save workflow file
            
        Returns:
            Workflow YAML content
        """
        workflow = {
            "name": "Mutation Testing",
            "on": {
                "push": {"branches": ["main", "master", "develop"]},
                "pull_request": {"branches": ["main", "master", "develop"]},
            },
            "permissions": {
                "contents": "read",
                "pull-requests": "write",
            },
            "jobs": {
                "mutation-testing": {
                    "runs-on": "ubuntu-latest",
                    "steps": [
                        {
                            "name": "Checkout code",
                            "uses": "actions/checkout@v4",
                        },
                        {
                            "name": "Set up Python",
                            "uses": "actions/setup-python@v5",
                            "with": {
                                "python-version": "3.11",
                            },
                        },
                        {
                            "name": "Install dependencies",
                            "run": "pip install -r requirements.txt",
                        },
                        {
                            "name": "Install TestForge",
                            "run": "pip install testforge",
                        },
                        {
                            "name": "Run mutation tests",
                            "id": "mutation",
                            "run": (
                                f"testforge run "
                                f"--threshold {self.config.threshold} "
                                f"--parallel {self.config.parallel_jobs} "
                                f"--format {self.config.report_format}"
                            ),
                            "continue_on_error": True,
                        },
                        {
                            "name": "Upload mutation report",
                            "if": "always()",
                            "uses": "actions/upload-artifact@v4",
                            "with": {
                                "name": "mutation-report",
                                "path": "mutation_report.html",
                                "retention-days": 30,
                            },
                        },
                        {
                            "name": "Comment on PR",
                            "if": "github.event_name == 'pull_request'",
                            "run": (
                                "testforge comment-pr "
                                "--token ${{ secrets.GITHUB_TOKEN }}"
                            ),
                        },
                    ],
                },
            },
        }
        
        yaml_str = yaml.dump(workflow, default_flow_style=False, sort_keys=False)
        
        if output_path:
            with open(output_path, "w") as f:
                f.write(yaml_str)
        
        return yaml_str
    
    def generate_gitlab_ci(
        self,
        project_root: Path,
        output_path: Optional[Path] = None,
    ) -> str:
        """
        Generate GitLab CI configuration for mutation testing.
        """
        config = f"""
mutation_testing:
  stage: test
  image: python:3.11-slim
  before_script:
    - pip install -r requirements.txt
    - pip install testforge
  script:
    - testforge run --threshold {self.config.threshold} --parallel {self.config.parallel_jobs} --format {self.config.report_format}
  artifacts:
    reports:
      junit: mutation-report.xml
    paths:
      - mutation_report.html
      - mutation_report.json
    expire_in: 30 days
  rules:
    - if: $CI_COMMIT_BRANCH == "main" || $CI_COMMIT_BRANCH == "master"
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
  timeout: {self.config.timeout}s
  allow_failure: false
"""
        
        if output_path:
            with open(output_path, "w") as f:
                f.write(config)
        
        return config
    
    def generate_jenkinsfile(
        self,
        project_root: Path,
        output_path: Optional[Path] = None,
    ) -> str:
        """
        Generate Jenkinsfile for mutation testing.
        """
        jenkinsfile = f'''
pipeline {{
    agent {{
        docker {{
            image 'python:3.11'
        }}
    }}
    
    stages {{
        stage('Mutation Testing') {{
            steps {{
                sh \'\'\'
                    pip install -r requirements.txt
                    pip install testforge
                    testforge run --threshold {self.config.threshold} --parallel {self.config.parallel_jobs} --format {self.config.report_format}
                \'\'\'
            }}
            
            post {{
                always {{
                    publishHTML(target: [
                        reportDir: '.',
                        reportFiles: 'mutation_report.html',
                        reportName: 'Mutation Report'
                    ])
                }}
            }}
        }}
    }}
    
    options {{
        timeout(time: {self.config.timeout}, unit: 'SECONDS')
    }}
}}
'''
        
        if output_path:
            with open(output_path, "w") as f:
                f.write(jenkinsfile)
        
        return jenkinsfile
    
    def generate_circle_ci(
        self,
        project_root: Path,
        output_path: Optional[Path] = None,
    ) -> str:
        """
        Generate CircleCI config for mutation testing.
        """
        config = {
            "version": 2.1,
            "orbs": {
                "python": "circleci/python@2.1.1",
            },
            "jobs": {
                "mutation-testing": {
                    "executor": "python/default",
                    "steps": [
                        "checkout",
                        "python/install-packages",
                        {
                            "run": {
                                "name": "Install TestForge",
                                "command": "pip install testforge",
                            }
                        },
                        {
                            "run": {
                                "name": "Run Mutation Tests",
                                "command": f"testforge run --threshold {self.config.threshold} --parallel {self.config.parallel_jobs}",
                            }
                        },
                        {
                            "store_test_results": {
                                "path": "test-results",
                            }
                        },
                        {
                            "store_artifacts": {
                                "path": "mutation_report.html",
                            }
                        },
                    ],
                },
            },
            "workflows": {
                "mutation-testing": {
                    "jobs": ["mutation-testing"],
                },
            },
        }
        
        yaml_str = yaml.dump(config, default_flow_style=False, sort_keys=False)
        
        if output_path:
            with open(output_path, "w") as f:
                f.write(yaml_str)
        
        return yaml_str
    
    def generate_azure_devops(
        self,
        project_root: Path,
        output_path: Optional[Path] = None,
    ) -> str:
        """
        Generate Azure DevOps pipeline for mutation testing.
        """
        yaml_str = f'''
trigger:
  - main
  - master

pool:
  vmImage: 'ubuntu-latest'

steps:
  - task: UsePythonVersion@0
    inputs:
      versionSpec: '3.11'

  - script: |
      pip install -r requirements.txt
      pip install testforge
    displayName: 'Install dependencies'

  - script: |
      testforge run --threshold {self.config.threshold} --parallel {self.config.parallel_jobs} --format {self.config.report_format}
    displayName: 'Run mutation tests'
    continueOnError: true

  - task: PublishTestResults@2
    condition: always()
    inputs:
      testResultsFiles: '**/test-results/*.xml'
      testRunTitle: 'Mutation Testing'

  - task: PublishBuildArtifacts@1
    inputs:
      pathToPublish: 'mutation_report.html'
      artifactName: 'Mutation Report'
'''
        
        if output_path:
            with open(output_path, "w") as f:
                f.write(yaml_str)
        
        return yaml_str
    
    def generate_pipeline(
        self,
        platform: CIPlatform,
        project_root: Path,
        output_path: Optional[Path] = None,
    ) -> str:
        """
        Generate pipeline configuration for the specified platform.
        """
        generators = {
            CIPlatform.GITHUB_ACTIONS: self.generate_github_actions,
            CIPlatform.GITLAB_CI: self.generate_gitlab_ci,
            CIPlatform.JENKINS: self.generate_jenkinsfile,
            CIPlatform.CIRCLE_CI: self.generate_circle_ci,
            CIPlatform.AZURE_DEVOPS: self.generate_azure_devops,
        }
        
        generator = generators.get(platform)
        if not generator:
            raise ValueError(f"Unsupported platform: {platform}")
        
        return generator(project_root, output_path)
    
    def generate_all_pipelines(
        self,
        project_root: Path,
        output_dir: Optional[Path] = None,
    ) -> Dict[str, str]:
        """
        Generate pipeline configurations for all supported platforms.
        """
        output_dir = output_dir or project_root
        
        configs = {}
        
        for platform in CIPlatform:
            try:
                output_path = output_dir / self._get_pipeline_filename(platform)
                content = self.generate_pipeline(platform, project_root, output_path)
                configs[platform.value] = content
            except Exception as e:
                configs[platform.value] = f"# Generation failed: {e}"
        
        return configs
    
    def _get_pipeline_filename(self, platform: CIPlatform) -> str:
        """Get the filename for a platform's pipeline configuration."""
        filenames = {
            CIPlatform.GITHUB_ACTIONS: ".github/workflows/mutation-testing.yml",
            CIPlatform.GITLAB_CI: ".gitlab-ci.yml",
            CIPlatform.JENKINS: "Jenkinsfile",
            CIPlatform.CIRCLE_CI: ".circleci/config.yml",
            CIPlatform.AZURE_DEVOPS: "azure-pipelines.yml",
        }
        return filenames.get(platform, "pipeline.yml")
    
    def create_github_pr_comment(
        self,
        score: float,
        total_mutations: int,
        killed: int,
        survived: int,
        recommendations: List[str],
    ) -> str:
        """
        Create a formatted comment for GitHub PR.
        """
        # Determine status emoji
        if score >= self.config.threshold:
            status_emoji = "✅"
            status_text = "PASSED"
        else:
            status_emoji = "❌"
            status_text = "FAILED"
        
        comment = f"""
## 🧪 TestForge Mutation Testing Results

{status_emoji} **Status: {status_text}**

| Metric | Value |
|--------|-------|
| **Mutation Score** | {score:.2f}% |
| **Threshold** | {self.config.threshold}% |
| **Total Mutations** | {total_mutations} |
| **Killed** | {killed} |
| **Survived** | {survived} |

"""
        
        if recommendations:
            comment += "### 💡 Recommendations\n\n"
            for rec in recommendations[:5]:
                comment += f"- {rec}\n"
        
        comment += f"\n---\n*Generated by TestForge*"
        
        return comment
    
    def parse_ci_environment(self) -> Dict[str, str]:
        """
        Parse CI environment variables to detect current platform.
        
        Returns:
            Dict with CI platform info
        """
        import os
        
        info = {
            "platform": "local",
            "is_ci": False,
            "pr_number": None,
            "commit_sha": None,
            "branch": None,
        }
        
        # GitHub Actions
        if os.getenv("GITHUB_ACTIONS"):
            info["platform"] = "github_actions"
            info["is_ci"] = True
            info["pr_number"] = os.getenv("PR_NUMBER")
            info["commit_sha"] = os.getenv("GITHUB_SHA")
            info["branch"] = os.getenv("GITHUB_REF_NAME")
        
        # GitLab CI
        elif os.getenv("GITLAB_CI"):
            info["platform"] = "gitlab_ci"
            info["is_ci"] = True
            info["commit_sha"] = os.getenv("CI_COMMIT_SHA")
            info["branch"] = os.getenv("CI_COMMIT_REF_NAME")
        
        # Jenkins
        elif os.getenv("JENKINS_URL"):
            info["platform"] = "jenkins"
            info["is_ci"] = True
            info["commit_sha"] = os.getenv("GIT_COMMIT")
            info["branch"] = os.getenv("GIT_BRANCH")
        
        # CircleCI
        elif os.getenv("CIRCLECI"):
            info["platform"] = "circle_ci"
            info["is_ci"] = True
            info["commit_sha"] = os.getenv("CIRCLE_SHA1")
            info["branch"] = os.getenv("CIRCLE_BRANCH")
        
        # Azure DevOps
        elif os.getenv("SYSTEM_TEAMFOUNDATIONCOLLECTIONURI"):
            info["platform"] = "azure_devops"
            info["is_ci"] = True
            info["commit_sha"] = os.getenv("BUILD_SOURCEVERSION")
            info["branch"] = os.getenv("BUILD_SOURCEBRANCHNAME")
        
        return info
