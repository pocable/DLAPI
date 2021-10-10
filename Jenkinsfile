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
  }

  post {
    always {
      junit 'nosetests.xml'
    }
  }
}