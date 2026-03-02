pipeline {
    agent any
    environment {
        HARBOR_REGISTRY = '10.0.0.225:8080'
        HARBOR_PROJECT = 'images'
        IMAGE_NAME = 'nginx'
        IMAGE_TAG = "v${BUILD_NUMBER}"
    }
    stages {
        stage('拉取代码') {
            steps {
                git url: 'https://github.com/zy666pink/jenkins-test.git',
                    credentialsId: 'zy666pink/******',
                    branch: '*/master'
            }
        }
        stage('构建镜像') {
            steps {
                sh 'docker build -t ${HARBOR_REGISTRY}/${HARBOR_PROJECT}/${IMAGE_NAME}:${IMAGE_TAG} .'
            }
        }
        stage('登录 Harbor') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'harbor-admin', passwordVariable: 'HARBOR_PWD', usernameVariable: 'HARBOR_USER')]) {
                    sh 'docker login ${HARBOR_REGISTRY} -u ${HARBOR_USER} -p ${HARBOR_PWD}'
                }
            }
        }
        stage('推送镜像') {
            steps {
                sh 'docker push ${HARBOR_REGISTRY}/${HARBOR_PROJECT}/${IMAGE_NAME}:${IMAGE_TAG}'
            }
        }
        stage('登出 Harbor') {
            steps {
                sh 'docker logout ${HARBOR_REGISTRY}'
            }
        }
    }
    post {
        success {
            echo '镜像构建并推送 Harbor 成功！'
        }
        failure {
            echo '构建或推送失败，请检查日志。'
        }
    }
}
