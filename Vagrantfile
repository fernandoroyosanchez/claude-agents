# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  # Use Ubuntu 22.04 LTS
  config.vm.box = "ubuntu/jammy64"

  config.vm.hostname = "claude-agents-test"

  # VM resources
  config.vm.provider "virtualbox" do |vb|
    vb.name = "claude-agents-test"
    vb.memory = "2048"
    vb.cpus = 2
  end

  # Sync the repo into the VM
  config.vm.synced_folder ".", "/home/vagrant/claude-agents"

  # Provisioning script
  config.vm.provision "shell", inline: <<-SHELL
    # Update system
    apt-get update

    # Install Python 3 and pip
    apt-get install -y python3 python3-pip python3-venv git

    # Install development tools
    apt-get install -y build-essential

    echo ""
    echo "=========================================="
    echo "  Claude Agents Test VM Ready"
    echo "=========================================="
    echo ""
    echo "The repository is available at: /home/vagrant/claude-agents"
    echo ""
    echo "To test the installation:"
    echo "  1. vagrant ssh"
    echo "  2. cd claude-agents"
    echo "  3. ./setup-agents.sh"
    echo ""
  SHELL
end
