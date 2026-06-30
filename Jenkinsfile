pipeline {
    agent any

    environment {
        IMAGE_NAME = "irynt"
        CONTAINER_NAME = "irynt-app"
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm

                sh '''
                echo "Latest Commit:"
                git log -1 --pretty=format:"%h | %an | %s"
                '''
            }
        }

        stage('Build') {
            steps {
                sh '''
                docker build \
                  -t ${IMAGE_NAME}:${BUILD_NUMBER} .
                '''
            }
        }

        stage('Deploy') {
            steps {
                sh '''
                   docker rm -f irynt-app || true

                   docker run -d \
                   --name irynt-app \
                   -p 5002:5000 \
                   ${IMAGE_NAME}:${BUILD_NUMBER}
                '''
            }
        }
    }
}

