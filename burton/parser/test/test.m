NSLocalizedString(@"SomeString", @"Translation for some key");
CFCopyLocalizedString("SomeOtherString", "Some other comment");
NSLocalizedStringFromTable("YetAnotherString", "SomeTable", nil);
CFCopyLocalizedStringFromTable("SomeString2", "SomeTable", "");
NSLocalizedStringFromTableInBundle(@"SomeOtherString2", nil, @"ATable", "");
CFCopyLocalizedStringFromTableInBundle("YetAnotherString2", "ATable", NULL, "");

// CustomFunctionLocalizedString(@"C++ Comment");

/*
Outside function
CustomFunctionLocalizedString(@"C Comment);
Another string outside function
*/

CustomFunctionLocalizedString(@"Custom String 1");
OtherFunctionLocalizedString(@"Custom String 2");