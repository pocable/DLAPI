pipeline {
  agent any
  environment {
    FLASK_APP = 'dlapi'
    FLASK_ENV = 'development'
    JD_DEVICE = credentials('JDownloaderDevice')
    RD_KEY = credentials('RealDebridAPIKey')
    API_KEY = 'thisisatestapikey'
    ENABLE_CORS_PROXY = true
    USER_PASS = 'test'
    SESSION_EXPIRY_DAYS = 1
    JD_USER = credentials('JDownloaderUser')
    JD_PASS = credentials('JDownloaderPass')
    JACKETT_URL = credentials('JackettURL')
    JACKETT_API_KEY = credentials('JackettAPIKey')
    DOCKERHUB_CREDENTIALS = credentials('dockerhub-login-pocable')

  }

  stages {
    stage('requirements') {
      steps {
        sh '''
        #!/bin/bash
        python3.9 -m pip install -r requirements.txt
        python3.9 -m pip install .
        '''
      }
    }

    stage('test') {
      steps {
        sh '''
        #!/bin/bash
        python3.9 -m nose --with-xunit
        '''
      }
    }

    stage('build') {
      steps {
        script {
          if(env.BRANCH_NAME == 'master'){
            sh 'docker build -t pocable/dlapi:latest .'
          } else if(env.BRANCH_NAME == 'beta'){
            sh 'docker build -t pocable/dlapi:edge .'
          } else {
            sh 'docker build -t pocable/dlapi .'
          }
        }
      }
    }

    stage('login') {
      steps {
        sh 'echo $DOCKERHUB_CREDENTIALS_PSW | docker login -u $DOCKERHUB_CREDENTIALS_USR --password-stdin'
      }
    }
    
    stage('deploy') {
      steps {
        script {
          if(env.BRANCH_NAME == 'master'){
            sh 'docker push pocable/dlapi:latest'
          } else if(env.BRANCH_NAME == 'beta'){
            sh 'docker push pocable/dlapi:edge'
          } else {
            echo 'Branch is not master/beta. Skipping deploy.'
          }
        }
      }
    }
  }

  post {
    always {
      sh 'docker logout'
      junit '**/nosetests.xml'
    }
  }
}