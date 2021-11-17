pipeline {
    agent any

    stages {
        stage('Copy Environment Variables') {
            steps {
                echo 'Building..'
                sh """
                sudo cp /etc/trippy/.env .env
                """
            }
        }

        stage('Deploy') {
            steps {
                echo 'Deploying....'
                sh """
                    chmod +x deploy.sh
                    sudo ./deploy.sh
                """
            }
        }
    }
}