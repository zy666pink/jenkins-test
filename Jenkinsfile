pipeline {
    agent any
    environment {
        HARBOR_REGISTRY = '10.0.0.225:80'
        HARBOR_PROJECT = 'docker-images'
        IMAGE_NAME = 'my-app'
        IMAGE_TAG = "${BUILD_NUMBER}"
        FULL_IMAGE_NAME = "${HARBOR_REGISTRY}/${HARBOR_PROJECT}/${IMAGE_NAME}:${IMAGE_TAG}"
    }
    stages {
        // 删掉重复的「拉取代码」stage，Declarative 会自动拉取

        stage('构建 Docker 镜像') {
            steps {
                sh "docker build -t ${FULL_IMAGE_NAME} ."
            }
        }

        stage('登录 Harbor 并推送镜像') {
            steps {
                script {
                    withCredentials([
                        usernamePassword(
                            credentialsId: 'harbor-cicd-token', // 确认这个Harbor凭据ID正确
                            usernameVariable: 'HARBOR_USER',
                            passwordVariable: 'HARBOR_PWD'
                        )
                    ]) {
                        sh "docker login ${HARBOR_REGISTRY} -u ${HARBOR_USER} -p ${HARBOR_PWD}"
                        sh "docker push ${FULL_IMAGE_NAME}"
                    }
                }
            }
        }
    }
    post {
        success {
            echo "镜像推送成功: ${FULL_IMAGE_NAME}"
            sh "docker rmi ${FULL_IMAGE_NAME} || true"
        }
        failure {
            echo "构建或推送失败，请检查日志"
        }
    }
}
