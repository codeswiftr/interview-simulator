import { useEffect } from 'react';
import { Link } from 'react-router-dom';

const LAST_UPDATED = 'March 22, 2026';

interface SectionProps {
  id: string;
  title: string;
  children: React.ReactNode;
}

function Section({ id, title, children }: SectionProps) {
  return (
    <section id={id} className="mb-10">
      <h2 className="text-xl font-semibold text-text-primary mb-4 pb-2 border-b border-border-light">
        {title}
      </h2>
      <div className="space-y-3 text-text-secondary leading-relaxed">{children}</div>
    </section>
  );
}

function SubSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="mt-5">
      <h3 className="text-base font-semibold text-text-primary mb-2">{title}</h3>
      <div className="space-y-2 text-text-secondary leading-relaxed">{children}</div>
    </div>
  );
}

export default function TermsPage() {
  useEffect(() => {
    document.title = 'Terms of Service | Interview Simulator — CodeSwiftr';
  }, []);

  return (
    <div className="min-h-screen bg-surface-primary py-12 px-4">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="mb-10">
          <p className="text-sm text-text-tertiary mb-2">Legal</p>
          <h1 className="text-3xl font-bold text-text-primary mb-3">Terms of Service</h1>
          <p className="text-text-secondary text-sm">
            Last updated: <span className="font-medium text-text-primary">{LAST_UPDATED}</span>
          </p>
          <p className="mt-4 text-text-secondary">
            These Terms of Service (&quot;Terms&quot;) govern your access to and use of the Interview
            Simulator service (&quot;Service&quot;) provided by CodeSwiftr, operated by Bogdan Veliscu
            (&quot;we&quot;, &quot;our&quot;, &quot;us&quot;), available at{' '}
            <a
              href="https://app.codeswiftr.com"
              className="text-electric-blue hover:underline"
              target="_blank"
              rel="noopener noreferrer"
            >
              app.codeswiftr.com
            </a>
            .
          </p>
          <p className="mt-3 text-text-secondary">
            By creating an account or using the Service, you agree to these Terms in full. If you do not
            agree, you must not use the Service. These Terms constitute a legally binding agreement
            between you and CodeSwiftr.
          </p>
        </div>

        {/* Table of Contents */}
        <div className="bg-surface-secondary border border-border-light rounded-xl p-5 mb-10">
          <p className="text-sm font-semibold text-text-primary mb-3">Table of Contents</p>
          <ol className="space-y-1.5 text-sm text-electric-blue list-decimal list-inside">
            {[
              ['#eligibility', 'Eligibility'],
              ['#accounts', 'Accounts and Registration'],
              ['#subscription', 'Subscription Plans and Billing'],
              ['#free-trial', 'Free Trial'],
              ['#cancellation', 'Cancellation and Refunds'],
              ['#acceptable-use', 'Acceptable Use Policy'],
              ['#audio-and-ai', 'Audio Recording and AI Processing'],
              ['#intellectual-property', 'Intellectual Property'],
              ['#your-content', 'Your Content and Data'],
              ['#data-retention', 'Data Retention and Deletion'],
              ['#availability', 'Service Availability'],
              ['#disclaimer', 'Disclaimer of Warranties'],
              ['#liability', 'Limitation of Liability'],
              ['#indemnification', 'Indemnification'],
              ['#governing-law', 'Governing Law and Disputes'],
              ['#changes', 'Changes to These Terms'],
              ['#contact', 'Contact Us'],
            ].map(([href, label]) => (
              <li key={href}>
                <a href={href} className="hover:underline">
                  {label}
                </a>
              </li>
            ))}
          </ol>
        </div>

        {/* Sections */}
        <Section id="eligibility" title="1. Eligibility">
          <p>
            You must be at least 16 years old to use the Service. By using the Service, you represent
            that you meet this age requirement. If you are using the Service on behalf of an
            organization, you represent that you have the authority to bind that organization to these
            Terms.
          </p>
          <p>
            The Service is intended for individual professional development and business use. Use of the
            Service for any unlawful purpose is strictly prohibited.
          </p>
        </Section>

        <Section id="accounts" title="2. Accounts and Registration">
          <p>
            To access most features of the Service, you must create an account. You agree to provide
            accurate, current, and complete information during registration and to keep your account
            information up to date.
          </p>
          <p>
            You are responsible for maintaining the confidentiality of your account credentials and for
            all activity that occurs under your account. You must notify us immediately at{' '}
            <a href="mailto:support@codeswiftr.com" className="text-electric-blue hover:underline">
              support@codeswiftr.com
            </a>{' '}
            if you suspect unauthorized access to your account.
          </p>
          <p>
            We reserve the right to suspend or terminate accounts that violate these Terms or that we
            reasonably suspect are involved in fraudulent or abusive activity.
          </p>
        </Section>

        <Section id="subscription" title="3. Subscription Plans and Billing">
          <p>
            The Service is offered under the following pricing tiers:
          </p>

          <SubSection title="Free Tier">
            <p>
              The Free tier includes a limited number of practice interviews (currently 3 sessions) at no
              charge. Free tier users have access to core interview practice features without AI feedback
              history beyond the current session.
            </p>
          </SubSection>

          <SubSection title="Pro Tier">
            <p>
              The Pro tier provides unlimited interview practice sessions, full AI feedback history,
              advanced analytics, and priority support. Pro is billed at{' '}
              <strong className="text-text-primary">$29/month</strong> (monthly billing) or{' '}
              <strong className="text-text-primary">$290/year</strong> (annual billing, equivalent to
              approximately $24/month). Prices are in USD and may be subject to applicable taxes.
            </p>
          </SubSection>

          <SubSection title="Team Tier">
            <p>
              The Team tier provides all Pro features plus team management, shared analytics, member
              invitations, and centralized billing. Team pricing is calculated per seat and is displayed
              during the upgrade flow. Team billing is managed through Stripe.
            </p>
          </SubSection>

          <p className="mt-4">
            All paid subscriptions are billed in advance on a recurring basis (monthly or annually)
            through Stripe. By subscribing, you authorize us to charge your payment method on file at
            the start of each billing period.
          </p>
          <p>
            Prices may change with 30 days' advance notice. Notice will be provided by email and/or
            in-app notification. Continued use of the Service after a price change constitutes
            acceptance of the new pricing.
          </p>
        </Section>

        <Section id="free-trial" title="4. Free Trial">
          <p>
            New Pro subscribers may be eligible for a{' '}
            <strong className="text-text-primary">7-day free trial</strong>. During the trial period,
            you have access to all Pro tier features at no charge.
          </p>
          <p>
            To start a free trial, a valid payment method is required. Your payment method will not be
            charged during the trial period. At the end of the 7-day trial, your subscription will
            automatically convert to a paid Pro subscription and your payment method will be charged
            unless you cancel before the trial ends.
          </p>
          <p>
            Free trials are available once per customer and per payment method. We reserve the right to
            determine trial eligibility at our discretion and to modify or discontinue free trial offers
            at any time.
          </p>
        </Section>

        <Section id="cancellation" title="5. Cancellation and Refunds">
          <SubSection title="5.1 Cancellation">
            <p>
              You may cancel your subscription at any time from your account Settings page or by
              contacting{' '}
              <a href="mailto:support@codeswiftr.com" className="text-electric-blue hover:underline">
                support@codeswiftr.com
              </a>
              . Upon cancellation, your subscription remains active until the end of the current billing
              period, after which your account will revert to the Free tier.
            </p>
            <p>
              Cancellation does not delete your account or your data. You may resubscribe at any time.
            </p>
          </SubSection>

          <SubSection title="5.2 Refunds">
            <p>
              All subscription fees are non-refundable except where required by applicable law. If you
              cancel during a free trial, you will not be charged.
            </p>
            <p>
              We may issue refunds or credits at our discretion in exceptional circumstances, such as
              material service outages or billing errors. To request a refund, contact{' '}
              <a href="mailto:support@codeswiftr.com" className="text-electric-blue hover:underline">
                support@codeswiftr.com
              </a>{' '}
              within 14 days of the charge in question.
            </p>
          </SubSection>

          <SubSection title="5.3 EU Statutory Rights">
            <p>
              If you are a consumer based in the European Union, you may have a statutory right to
              withdraw from a subscription within 14 days of purchase (the &quot;cooling-off period&quot;),
              provided you have not used the Service during that period. By using the Service immediately
              after subscribing, you expressly request early access and acknowledge that your right of
              withdrawal is waived upon first use.
            </p>
          </SubSection>
        </Section>

        <Section id="acceptable-use" title="6. Acceptable Use Policy">
          <p>
            You agree to use the Service only for lawful purposes and in accordance with these Terms. You
            must not:
          </p>
          <ul className="list-disc list-inside space-y-2 ml-2 mt-2">
            <li>
              Share, resell, or sublicense access to the Service without our written permission
            </li>
            <li>
              Use the Service to record content that contains hateful, discriminatory, defamatory, or
              sexually explicit material
            </li>
            <li>
              Attempt to reverse-engineer, decompile, or extract source code from the Service
            </li>
            <li>
              Use automated scripts, bots, or scraping tools to access the Service in a manner that
              exceeds normal usage
            </li>
            <li>
              Attempt to gain unauthorized access to other users&apos; accounts, data, or our
              infrastructure
            </li>
            <li>
              Use the Service to process audio recordings of individuals who have not consented to being
              recorded
            </li>
            <li>
              Interfere with or disrupt the integrity or performance of the Service or third-party data
              contained therein
            </li>
            <li>
              Violate any applicable local, national, or international law or regulation
            </li>
          </ul>
          <p className="mt-3">
            Violation of this Acceptable Use Policy may result in immediate suspension or termination of
            your account without refund. We reserve the right to report suspected illegal activity to
            relevant law enforcement authorities.
          </p>
        </Section>

        <Section id="audio-and-ai" title="7. Audio Recording and AI Processing">
          <SubSection title="7.1 Your Consent to Recording">
            <p>
              By using the interview recording feature, you consent to your audio being captured,
              transmitted, and processed. You represent that you are the sole speaker in any recording
              you submit, or that you have obtained all necessary consents from other speakers.
            </p>
          </SubSection>

          <SubSection title="7.2 Transcription">
            <p>
              Audio recordings are transcribed to text using OpenAI&apos;s Whisper API. Transcription
              accuracy depends on audio quality, accent, and background noise. We do not guarantee
              perfect transcription accuracy.
            </p>
          </SubSection>

          <SubSection title="7.3 AI Feedback">
            <p>
              Transcribed text is analyzed by Anthropic&apos;s Claude AI to generate feedback scores,
              suggestions, and performance summaries. AI-generated feedback is provided as an informational
              tool to support your professional development. It is{' '}
              <strong className="text-text-primary">not a guarantee</strong> of interview success or
              employability, and should not be relied upon as a substitute for professional career
              coaching.
            </p>
          </SubSection>

          <SubSection title="7.4 No AI Training on Your Data">
            <p>
              We do not use your audio recordings, transcriptions, or AI-generated feedback to train
              our own AI models. We transmit this data to OpenAI and Anthropic solely for the purpose of
              generating your feedback, subject to their respective API data policies.
            </p>
          </SubSection>
        </Section>

        <Section id="intellectual-property" title="8. Intellectual Property">
          <SubSection title="8.1 Our IP">
            <p>
              The Service, including its software, design, user interface, question database, and
              branding, is owned by CodeSwiftr and protected by copyright, trademark, and other
              intellectual property laws. You may not copy, reproduce, or create derivative works of any
              part of the Service without our express written consent.
            </p>
          </SubSection>

          <SubSection title="8.2 Your Feedback and Suggestions">
            <p>
              If you provide us with feedback, suggestions, or ideas about the Service, you grant us an
              irrevocable, worldwide, royalty-free license to use that feedback for any purpose without
              compensation to you.
            </p>
          </SubSection>
        </Section>

        <Section id="your-content" title="9. Your Content and Data">
          <p>
            You retain ownership of the audio recordings and answers you submit to the Service
            (&quot;Your Content&quot;). By using the Service, you grant CodeSwiftr a limited,
            non-exclusive license to process, store, and transmit Your Content solely to provide the
            Service to you.
          </p>
          <p>
            This license does not permit us to use Your Content for any purpose other than operating and
            improving the Service as described in these Terms and our Privacy Policy.
          </p>
          <p>
            You are responsible for ensuring that Your Content does not infringe any third-party rights,
            including intellectual property rights, privacy rights, or applicable laws.
          </p>
        </Section>

        <Section id="data-retention" title="10. Data Retention and Deletion">
          <p>
            You may delete individual interview sessions from your account at any time. You may also
            delete your entire account from the Settings page, which will trigger deletion of your
            personal data in accordance with our{' '}
            <Link to="/privacy" className="text-electric-blue hover:underline">
              Privacy Policy
            </Link>
            .
          </p>
          <p>
            Certain data, such as billing records, may be retained for the period required by applicable
            tax and accounting law (typically 7 years in the EU) even after account deletion.
          </p>
        </Section>

        <Section id="availability" title="11. Service Availability">
          <p>
            We aim to provide the Service with high availability but do not guarantee uninterrupted
            access. The Service may be temporarily unavailable due to maintenance, infrastructure
            failures, or factors outside our control.
          </p>
          <p>
            We are not liable for losses arising from Service downtime. We will make reasonable efforts
            to notify users of planned maintenance in advance.
          </p>
        </Section>

        <Section id="disclaimer" title="12. Disclaimer of Warranties">
          <p>
            The Service is provided on an &quot;as is&quot; and &quot;as available&quot; basis without
            warranties of any kind, either express or implied, including but not limited to implied
            warranties of merchantability, fitness for a particular purpose, or non-infringement.
          </p>
          <p>
            We do not warrant that the Service will meet your specific requirements, that AI-generated
            feedback will be accurate or complete, or that the Service will be error-free or
            uninterrupted.
          </p>
          <p>
            Nothing in these Terms affects any statutory rights you may have as a consumer under EU
            consumer protection law.
          </p>
        </Section>

        <Section id="liability" title="13. Limitation of Liability">
          <p>
            To the fullest extent permitted by applicable law, CodeSwiftr and its operators shall not be
            liable for any indirect, incidental, special, consequential, or punitive damages, including
            but not limited to loss of profits, data, or goodwill, arising from your use of or inability
            to use the Service.
          </p>
          <p>
            Our total aggregate liability to you for any claim arising from these Terms or your use of
            the Service shall not exceed the greater of (a) the total subscription fees paid by you in
            the 3 months immediately preceding the claim, or (b) €50.
          </p>
          <p>
            These limitations apply regardless of the theory of liability (contract, tort, statute, or
            otherwise) and even if we have been advised of the possibility of such damages.
          </p>
          <p>
            Nothing in these Terms limits or excludes liability for fraud, gross negligence, willful
            misconduct, or any liability that cannot be excluded by law.
          </p>
        </Section>

        <Section id="indemnification" title="14. Indemnification">
          <p>
            You agree to indemnify, defend, and hold harmless CodeSwiftr and its operators from and
            against any claims, damages, losses, costs, and expenses (including reasonable legal fees)
            arising from:
          </p>
          <ul className="list-disc list-inside space-y-1.5 ml-2 mt-2">
            <li>Your use of the Service in violation of these Terms</li>
            <li>Your Content, including any claims that Your Content infringes third-party rights</li>
            <li>Your violation of any applicable law or regulation</li>
          </ul>
        </Section>

        <Section id="governing-law" title="15. Governing Law and Disputes">
          <p>
            These Terms are governed by and construed in accordance with the laws of the European Union
            and applicable EU member state law. Any disputes arising from these Terms or your use of the
            Service shall be subject to the exclusive jurisdiction of the courts of the EU member state
            in which the operator is established.
          </p>
          <p>
            If you are a consumer in the EU, you also have the right to use the EU Online Dispute
            Resolution platform at{' '}
            <a
              href="https://ec.europa.eu/consumers/odr"
              className="text-electric-blue hover:underline"
              target="_blank"
              rel="noopener noreferrer"
            >
              ec.europa.eu/consumers/odr
            </a>
            .
          </p>
          <p>
            Nothing in this clause affects your statutory rights as an EU consumer.
          </p>
        </Section>

        <Section id="changes" title="16. Changes to These Terms">
          <p>
            We may update these Terms from time to time. When we make material changes, we will notify
            you by email or by displaying a prominent notice in the application at least 14 days before
            the changes take effect.
          </p>
          <p>
            If you do not agree to the updated Terms, you must stop using the Service before the
            effective date. Continued use of the Service after that date constitutes acceptance of the
            revised Terms.
          </p>
        </Section>

        <Section id="contact" title="17. Contact Us">
          <p>
            If you have questions about these Terms or need to report a legal matter, please contact us:
          </p>
          <div className="bg-surface-secondary border border-border-light rounded-lg p-4 mt-3 text-sm space-y-1">
            <p className="text-text-primary font-medium">CodeSwiftr — Legal</p>
            <p>Operated by: Bogdan Veliscu</p>
            <p>
              Email:{' '}
              <a href="mailto:support@codeswiftr.com" className="text-electric-blue hover:underline">
                support@codeswiftr.com
              </a>
            </p>
            <p>
              Subject line:{' '}
              <span className="text-text-primary">Terms Enquiry — [your name]</span>
            </p>
          </div>
        </Section>

        {/* Footer nav */}
        <div className="mt-12 pt-6 border-t border-border-light flex flex-wrap gap-4 text-sm text-text-tertiary">
          <Link to="/" className="hover:text-electric-blue transition-colors">
            Home
          </Link>
          <Link to="/privacy" className="hover:text-electric-blue transition-colors">
            Privacy Policy
          </Link>
          <a href="mailto:support@codeswiftr.com" className="hover:text-electric-blue transition-colors">
            Contact
          </a>
        </div>
      </div>
    </div>
  );
}
