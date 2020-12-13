pipeline {
  agent any
  stages {
    stage('Docker Setup') {
      steps {
        sh "aws ecr get-login-password --region eu-west-1 | docker login --username AWS --password-stdin 254010146609.dkr.ecr.eu-west-1.amazonaws.com"
      }
    }
    stage('Linter') {
      agent {
        docker {
          image '254010146609.dkr.ecr.eu-west-1.amazonaws.com/ubuntu:18.04'
          args '-u root'
        }
      }
      steps {
        echo 'Starting linter'
        sh """whoami && apt update && apt install shellcheck pylint python-pytest -y && ./ci.sh"""
        }
      }
  }
}

