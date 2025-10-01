#!/usr/bin/perl
# This is a hook script to be able to establish a mirroring bridge for Security Onion to analyze traffic 
use strict; 
use warnings;

my $vmid = shift;
my $phase = shift;

print "GUEST BRIDGE MIRROR HOOK: " . join(' ', @ARGV). "\n";

sub MirrorSourceToDestination
{
    my $src = $_[0];
    my $des = $_[1];
    my $uid = $_[2];

    print "Creating INGRESS qdisc for $src \n";
    system("tc", "qdisc", "add", "dev", "$src", "ingress");

    print "Creating INGRESS filter for $src to $des \n";
    system("tc", "filter", "add", "dev", "$src", "parent", "ffff:0",
           "protocol", "all",
           "u32", "match", "u8", "0", "0",
           "action", "mirred", "egress", "mirror", "dev", "$des");

    print "Creating EGRESS qdisc for $src \n";
    system("tc", "qdisc", "add", "dev", "$src", "handle", "$uid:0", "root", "prio" );

    print "Creating EGRESS filter for $src to $des \n";
    system("tc", "filter", "add", "dev", "$src", "parent", "$uid:0",
           "protocol", "all",
           "u32", "match", "u8", "0", "0",
           "action", "mirred", "egress", "mirror", "dev", "$des");

    print "Turning on $src promiscuous mode \n";
    system("ip", "link", "set", "$src", "promisc", "on");
}

sub RemoveMirror
{
    my $target = $_[0];

    print "Removing INGRESS mapping from $target \n";
    system("tc", "qdisc", "del", "dev", "$target", "ingress" );

    print "Removing EGRESS mapping from $target \n";
    system("tc", "qdisc", "del", "dev", "$target", "root" );

    print "Turning off $target promiscuous mode \n";
    system("ip", "link", "set", "$target", "promisc", "on");
}

if ($phase eq 'pre-start') {
    MirrorSourceToDestination("vmbr2", "vmbr4", "10");
    MirrorSourceToDestination("vmbr0", "vmbr5", "20");
} elsif ($phase eq 'pre-stop') {
    RemoveMirror("vmbr2");
    RemoveMirror("vmbr5");
}
