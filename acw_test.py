#!/usr/bin/env python

from subprocess import PIPE, Popen
import argparse
import sys
import json
import pipes

inCommandList = {
"CustomerGateways": ["describe-customer-gateways", ".CustomerGateways[].CustomerGatewayId"] ,
"DhcpOptions": ["describe-dhcp-options", ".DhcpOptions[].DhcpOptionsId"] ,
"Images": ["describe-images", ".Images[].ImageId"] ,
"InternetGateways": ["describe-internet-gateways", ".InternetGateways[].InternetGatewayId"],
"NetworkAcls": ["describe-network-acls", ".NetworkAcls[].NetworkAclId"],
"NetworkInterfaces": ["describe-images", ".NetworkAcls[].NetworkAclId"],
"Reservations": ["describe-instances", ".Reservations[].Instances[].InstanceId"],
"ReservedInstances": ["describe-reserved-instances", ".ReservedInstances[].ReservedInstancesId"],
"RouteTables": ["describe-route-tables", ".RouteTables[].RouteTableId"],
"SecurityGroups": ["describe-security-groups", ".SecurityGroups[].GroupId"],
"Snapshots": ["describe-snapshots", ".Snapshots[].SnapshotId"],
"SpotInstanceRequests": ["describe-spot-instance-requests", ".SpotInstanceRequests[].SpotInstanceRequestId"],
"Subnets": ["describe-subnets", ".Subnets[].SubnetId"],
"Volumes": ["describe-volumes", ".Volumes[].VolumeId"],
"VpcPeeringConnections": ["describe-vpc-peering-connections", ".VpcPeeringConnections[].VpcPeeringConnectionId"],
"Vpcs": ["describe-vpcs", ".Vpcs[].VpcId"],
"VpnConnections": ["describe-vpn-connections", ".VpnConnections[].VpnConnectionId"],
"VpnGateways": ["describe-vpn-gateways", ".VpnGateways[].VpnGatewayId"]
}

outCommandList = {
"describe-instance-attribute": ["--instance-id", "%"],
"describe-instance-status": ["--instance-id", "%"],
"monitor-instances": ["--instance-id", "%"],
"reboot-instances": ["--instance-id", "%"],
"start-instances": ["--instance-id", "%"],
"stop-instances": ["--instance-id", "%"],
"terminate-instances": ["--instance-id", "%"],
"unmonitor-instances": ["--instance-id", "%"],
"get-console-output": ["--instance-id", "%"]
}

def searchJSON(node, search, result):
	if isinstance(node, dict):
		for k in node.keys():
			if search in k:
				if k not in result:
					result[k] = node[k]
				elif isinstance(result[k], basestring):
					result[k] = [result[k], node[k]]
				else:
					result[k] = [result[k].append(node[k])]
			else:
				searchJSON(node[k], search, result)
	elif isinstance(node, list):
		for i in range(len(node)):
			if search in node[i]:
				result[i] = node[i]
			else:
				searchJSON(node[i], search, result)
	else:
		pass
	return result

def filterJSON(data, search):
	filteredJSON = {"Resources": []}
	for node in data[data.keys()[0]]:
		out = {}
	 	filteredJSON["Resources"].append(searchJSON(node, search, out))
	return json.dumps(filteredJSON)

def runPipeLine(data, commands):
	p = pipes.Template()
	for command in commands:
		p.append(command, '--')
	i = p.open('pipeIn', 'w')
	i.write(data)
	i.close()
	return open('pipeIn').read()

parser = argparse.ArgumentParser()
parser.add_argument('-c', nargs ='*')
parser.add_argument('-s')
args = parser.parse_args()

outCommandArgs = [a for a in args.c[0].split(' ')]
searchArg = args.s

# Try to load the stdin as JSON.
try:
	pipeData = json.load(sys.stdin)
except ValueError:
	print "This input doesn't look like JSON. What's the deal?"
	sys.exit()


# Identify the input.
try:
	fromCommand = inCommandList[pipeData.keys()[0]][0]
	jqSelection = inCommandList[pipeData.keys()[0]][1]
except KeyError, err:
	print "I didn't find any valid keys in the input JSON."
	print "The top level key found was:" 
	print "    * " + pipeData.keys()[0]
	print "Valid top level keys are:"
	for k in inCommandList.keys():
		print "    * " + k + " from " + inCommandList[k][0]
	sys.exit() 

if searchArg:
	filterData = filterJSON(pipeData, "Id")
	jqSelection = ".Resources[]." + searchArg
else:
	filterData = json.dumps(pipeData)

outCommand = outCommandArgs.pop(0)

# Parses instance-ids out of describe-instances input.
command1 = ["jq", "-r", jqSelection]
command2 = ["xargs", "-I", "%", "aws", "ec2", outCommand]
command2.extend(outCommandList[outCommand])
command2.extend(outCommandArgs)
someCommands = [" ".join(command1), " ".join(command2)]

# Final output.
print runPipeLine(filterData, someCommands)
