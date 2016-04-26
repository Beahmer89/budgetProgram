#! /usr/bin/perl
use strict;
use warnings;
use Data::Dumper;
use Getopt::Long;
use Params::Validate qw(:all);
use Scalar::Util qw(looks_like_number);
use POSIX qw(strftime);

use XML::Simple;

my $filename = 'finances.csv';
my $base_yr = 2015;
my $data; 
my $year; 
my $month; 
my $begin;
my $account; 

#No args will get you print out transactions per month for all years
#   Month arg will get you specific month with all transactions
#   year arg will get you specific year with all transactions
#   month && year will get you specific transactions for that month for particular year
#cmp eventually would like to get totals for the years

#put these in a hash so I dont have to have multiple if statements doing the same thing
my @months = ('January','February','March','April','May','June','July','August','September','October','November','December');

GetOptions (
    "month|m=s" => \$month,
    "year|y=s"  => \$year,
    "account|a" => \$account,
);

#get the digit for the month
if ( defined( $month ) ) {

    for ( my $i=0;$i < scalar(@months); $i++ ) {
        if ( lc( $months[$i] ) eq lc( $month ) ) {
            $month = ++$i;
            last;
        }
    }
    if ( ! looks_like_number($month) ) {
        die "Does not the month is correct \n";
    }
}

main();

sub main {
    $data = getXMLFile();
    my ( $categories, $id ) = getCategoryInfo(data => $data); 
    my $transactions = getTransactionInfo(data => $data); 
    createCSV(trans => $transactions, accounts => $categories, account_id => $id);
}

sub getXMLFile {
    
    #TODO needs to be for anyone
    my $filename = `ls ../xml/ -t | head -1`;
    chomp $filename;

    my $xml = new XML::Simple;
    return my $info = $xml->XMLin("../xml/$filename", ContentKey => 'id', SuppressEmpty => 1);
}

sub getCategoryInfo {

    my %params = validate(@_,{data => {type => HASHREF}});

    my %accounts;
    my $accnt_id;
    my $cat = $params{data}->{'gnc:book'}->{'gnc:account'};

    for(my $i=0;$i<scalar(@{$cat});$i++) {
        if ( $cat->[$i]->{'act:type'} eq 'EXPENSE' ) {
            $accounts{$cat->[$i]->{'act:id'}->{id}} = $cat->[$i]->{'act:name'};
        }
    }

    if($account) {
        print "\nPlease select from one of the Following Categories: \n\n";
        foreach my $acct (sort {$a cmp $b} values %accounts) {
            print $acct . "\n";
        }
        print "\n";
        my $selection = <STDIN>;
        chomp $selection;

        foreach my $id (sort { $accounts{$a} cmp $accounts{$b} } keys %accounts) {
           if (lc( $accounts{$id} ) eq lc( $selection) ) {
                   $accnt_id = $id;
           }
        }

        if ( !$accnt_id ) {
            die "Sorry, selection entered was not in Account list. Please try again\n";
        }
        
    }

    #print Dumper(\%accounts);
    return \%accounts, $accnt_id;
}

sub getTransactionInfo {

    my %params = validate(@_,{data => {type => HASHREF}});

    my %transactions;
    my @skip = [];
    my $trans =  $params{data}->{'gnc:book'}->{'gnc:transaction'};
    my $x=0;


    for( my $i=0;$i<scalar(@{$trans});$i++ ) {

        #skip Paycheck and other transactions not needed for this program
        if ( $trans->[$i]->{'trn:description'} !~ /Paycheck/ ) {

            #print $trans->[$i]->{'trn:description'} . "\n";
            #creating hash of hashs and will add create key for transactions and keys for new hashs
            $transactions{$trans->[$i]->{'trn:description'}}{$trans->[$i]->{'trn:id'}->{id}} = [];

            #add date posted to the array for each transaction
            push $transactions{$trans->[$i]->{'trn:description'}}{$trans->[$i]->{'trn:id'}->{id}}, $trans->[$i]->{'trn:date-posted'};
            for( my $x=0;$x<scalar(@{$trans->[$i]->{'trn:splits'}->{'trn:split'}});$x++ ) {
                #do not collect the negative quantities, they are not needed
                if ( $trans->[$i]->{'trn:splits'}->{'trn:split'}->[$x]->{'split:quantity'} !~ /\-/ ) {
                    push $transactions{$trans->[$i]->{'trn:description'}}{$trans->[$i]->{'trn:id'}->{id}}, $trans->[$i]->{'trn:splits'}->{'trn:split'}->[$x];
                }
            }
        }
    }

    #print Dumper(\%transactions);
    return \%transactions;
}

sub createCSV {
    my %params = validate(@_, {
           trans      => { type => HASHREF },
           accounts   => { type => HASHREF },
           account_id => { type => SCALAR|UNDEF },
        });

    my $transactions;

    foreach my $place (keys $params{trans}) {

        foreach my $trans ( values %{$params{trans}->{$place}} ){
            if ( scalar(@{$trans}) > 2 ) {
                die "Error:Amount of info for Transactions is more than expected for: "
                . $place . "Amount of info: "
                . scalar(@{$trans}) . "\n";
            }else {
                #push the name of the place, date of transaction and value onto array
                my @tmp;
                push(@tmp,$place);
                push(@tmp,$trans->[0]->{'ts:date'});
                push(@tmp,'='.$trans->[1]->{'split:value'});

                #check to see if the account idea is in the list of accounts
                if ( exists($params{accounts}->{$trans->[1]->{'split:account'}->{id}}) ) {
                    push(@tmp,$params{accounts}->{$trans->[1]->{'split:account'}->{id}});
                }else {
                    #if its not, go on
                    next;
                }

                #if the account param is specified, then do not include anything else execpt specified account
                if ( $account && defined($params{account_id}) ) {
                    #printf("Comparing %s = %s\n",$trans->[1]->{'split:account'}->{id},$params{account_id});
                    if ( $trans->[1]->{'split:account'}->{id} ne $params{account_id} ) {
                        next;
                    }
                }

                #split date
                my @date = split(/-/,$trans->[0]->{'ts:date'});

                #if the index at position 0 of the date contains a 0
                #This is so its easier to reference position in array
                if (index($date[1],0) == 0) {
                    #remove the beginning zero and replace with nothing
                    $date[1] =~ s/^[0]//;
                }

                #join them for the row
                my $info = join(',',@tmp);
                push(@{$transactions->{$date[0]}->{$date[1]}},$info);
                @tmp=();

            }
        }
    } 

    #remove filename if already present
    if ( -f $filename ) {
        print "Removing $filename....\n";
        my $rm = `rm $filename`;
        if ($rm) {
            die "There was an error removing $filename \n";
        }
    }

    #create new one
    my $cmd = `touch $filename`;

    #open file
    open( my $row, '>>', $filename ) or die "could not open $filename"; 

    if ( ( defined($year) && !defined($month) ) ||
        ( !defined($year) && !defined($month) ) ) {

        if ( !defined($year) ) {
            $year = strftime("%Y",localtime);
        }else {
            $base_yr = $year;
        }

        $month = strftime("%m",localtime);
        $month =~ s/^[0]//;

        for(my $i=$year;$i>=$base_yr;$i--){
            print $i ."\n";
            #if i is less than the current year
            if ($i < $year) {
                $month = 12;
            }

            for(my $j=$month;$j>0;$j--) {
                print $j . "\n";
                my $header = $j;
                #print month as header
                print {$row} uc($months[--$header]) . ' '. $i . "\n" or die "Error Writing Month to File!!\n";
                if ( exists($transactions->{$i}->{$j}) ) {
                    foreach my $trans (@{$transactions->{$i}->{$j}}) {
                        print {$row} $trans . "\n" or die "Error Writing Transactions to File!!\n";
                    }
                }
                print {$row} "\n\n";
            }

        }

    }else {

        my $header = $month;
        if ( exists($transactions->{$year}) ) {
            print {$row} uc($months[--$header]) . ' ' . $year . "\n" or die "Error Writing Month to File!!\n";
            foreach my $trans (@{$transactions->{$year}->{$month}}) {
                print {$row} $trans . "\n" or die "Error Writing Transactions to File!!\n";
            }

        }else {
            die "Could not find transactions for $year\n";
        }
    }

    close $row;
    print 'done' . "\n";
}
